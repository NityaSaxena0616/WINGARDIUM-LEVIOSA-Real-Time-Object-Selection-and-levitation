"""
===============================================================================
✦ WINGARDIUM LEVIOSA — Real-Time Magic Vision System ✦
Main Application Entrypoint
===============================================================================
"""

import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
import cv2

# Project Modules
from config.settings import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
    SPELL_LEVIOSA,
    SPELL_ACCIO,
    SPELL_EXPELLIARMUS,
    SPELL_FINITE,
)
from camera.camera import CameraStream
from tracking.hand_tracker import HandTracker
from tracking.wand_tracker import WandTracker
from detection.object_detector import ObjectDetector
from segmentation.object_segmenter import ObjectSegmenter
from processing.background import BackgroundReconstructor
from processing.transformations import ObjectTransformer
from magic.spell_controller import SpellController
from speech.speech_controller import SpeechController
from processing.effects import ParticleSystem, WandLightTrail
from processing.compositing import SceneCompositor
from ui.interface import MagicVisionUI


class WingardiumLeviosaApp:
    """
    Main Application Controller for Wingardium Leviosa.
    Coordinates video pipeline, tracking, segmentation, background reconstruction, physics, effects, and GUI.
    """

    def __init__(self, root):
        self.root = root

        # Pipeline Components
        self.camera = CameraStream(width=FRAME_WIDTH, height=FRAME_HEIGHT)
        self.hand_tracker = HandTracker()
        self.wand_tracker = WandTracker()
        self.detector = ObjectDetector()
        self.bg_reconstructor = BackgroundReconstructor()
        self.spell_controller = SpellController()
        self.particle_system = ParticleSystem()
        self.wand_trail = WandLightTrail()
        self.latest_frame = None
        self.last_hand_data = {}
        self.spell_queue = Queue()
        self.deselect_queue = Queue()
        self.selection_executor = ThreadPoolExecutor(max_workers=1)
        self.selection_future = None
        self.pending_spell = None

        # Voice Controller
        self.speech_controller = SpeechController(spell_callback=self.on_spell_command)
        self.speech_controller.start_listening()

        # UI
        self.ui = MagicVisionUI(
            root=self.root,
            on_spell_cast=self.on_spell_command,
            on_bg_capture=self.on_bg_capture,
            on_click_select=self.on_click_select,
            on_deselect=self.on_deselect,
            on_debug_toggle=self.on_debug_toggle
        )

        self.debug_mode = False
        self.is_running = True
        self.last_time = time.perf_counter()

        # Initial Background Capture after 5 frames to stabilize camera auto-exposure
        self.init_frames = 0
        self.frame_count = 0

        # Start Main Render Loop
        self.root.after(20, self._render_loop)

    def on_bg_capture(self):
        """Captures clean reference background frame."""
        if self.latest_frame is None:
            return False
        return self.bg_reconstructor.capture_background(self.latest_frame)

    def on_click_select(self, click_pt):
        """Selects object at clicked pixel coordinates (x, y)."""
        if self.latest_frame is None:
            self.ui.show_notice("Waiting for camera frame...")
            return

        if self.selection_future is not None:
            self.ui.show_notice("Object selection is already running...")
            return
        self.ui.show_notice("Selecting object...")
        self.selection_future = self.selection_executor.submit(
            self._select_object, self.latest_frame.copy(), click_pt
        )

    def on_spell_command(self, spell_name):
        """Queues spell commands so speech and UI callbacks never mutate app state."""
        self.spell_queue.put(spell_name)

    def on_deselect(self):
        """Queues deselection for the render thread."""
        self.deselect_queue.put(True)

    def _process_deselect_requests(self):
        try:
            self.deselect_queue.get_nowait()
        except Empty:
            return

        self.pending_spell = None
        if self.selection_future is not None:
            self.selection_future.cancel()
            self.selection_future = None
        while True:
            try:
                self.spell_queue.get_nowait()
            except Empty:
                break
        self.spell_controller.clear_selection()
        self.hand_tracker.reset_circle_selection()
        self.detector.selected_bbox = None
        self.detector.selected_seed_point = None
        self.detector.selected_label = "OBJECT"
        self.particle_system.particles.clear()
        self.ui.show_notice("Object deselected")

    @staticmethod
    def _select_object(frame, target_pt=None, selection_bounds=None):
        detector = ObjectDetector()
        if selection_bounds is not None:
            x, y, width, height = selection_bounds
            frame_height, frame_width = frame.shape[:2]
            x1 = max(0, min(frame_width - 1, int(x)))
            y1 = max(0, min(frame_height - 1, int(y)))
            x2 = max(x1 + 1, min(frame_width, int(x + width)))
            y2 = max(y1 + 1, min(frame_height, int(y + height)))
            bbox = (x1, y1, x2 - x1, y2 - y1)
            seed_point = (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2)
        else:
            bbox = detector.select_at_point(frame, target_pt)
            seed_point = target_pt
        if bbox is None:
            return None

        mask, extracted_bgra = ObjectSegmenter().segment(
            frame, bbox, use_grabcut=True, seed_point=seed_point
        )
        if mask is None or extracted_bgra is None:
            return None
        return bbox, mask, extracted_bgra

    def _start_circle_selection(self, frame, circle_bounds):
        if (circle_bounds is None or self.selection_future is not None
                or (self.spell_controller.has_selected_object
                    and self.spell_controller.physics.is_detached)):
            return

        self.pending_spell = SPELL_LEVIOSA
        self.ui.show_notice("Circle detected - selecting and lifting...")
        self.selection_future = self.selection_executor.submit(
            self._select_object, frame.copy(), None, circle_bounds
        )

    def _finish_selection(self):
        if self.selection_future is None or not self.selection_future.done():
            return

        future = self.selection_future
        self.selection_future = None
        try:
            result = future.result()
        except Exception as error:
            print(f"[WingardiumLeviosaApp] Object selection failed: {error}")
            self.ui.show_notice("Object selection failed", "#e63946")
            self.pending_spell = None
            return

        if result is None:
            self.ui.show_notice("No object found - click closer to its center", "#e63946")
            self.pending_spell = None
            return

        bbox, mask, extracted_bgra = result
        self.detector.selected_bbox = bbox
        self.detector.selected_label = "OBJECT"
        self.spell_controller.select_object(bbox, mask, extracted_bgra)
        if not self.bg_reconstructor.is_captured:
            self.bg_reconstructor.capture_background(self.latest_frame)
        self.ui.show_notice("Object selected", "#2ec4b6")

        if self.pending_spell is not None:
            self.spell_controller.cast_spell(
                self.pending_spell,
                hand_data=self.last_hand_data,
                frame_size=(self.latest_frame.shape[1], self.latest_frame.shape[0])
            )
            self.pending_spell = None

    def _process_spell_commands(self, frame):
        while True:
            try:
                spell_name = self.spell_queue.get_nowait()
            except Empty:
                break

            if self.spell_controller.has_selected_object:
                self.spell_controller.cast_spell(
                    spell_name,
                    hand_data=self.last_hand_data,
                    frame_size=(frame.shape[1], frame.shape[0])
                )
                continue

            if self.selection_future is not None:
                self.pending_spell = spell_name
                continue

            if spell_name == SPELL_FINITE:
                self.ui.show_notice("Select an object before casting", "#e63946")
                continue

            target_pt = self.last_hand_data.get("pointing_ray_end")
            if target_pt is None:
                target_pt = (int(frame.shape[1] * 0.5), int(frame.shape[0] * 0.7))
            self.pending_spell = spell_name
            self.ui.show_notice("Finding an object to target...")
            self.selection_future = self.selection_executor.submit(
                self._select_object, frame.copy(), target_pt
            )

    def on_debug_toggle(self, enabled):
        self.debug_mode = enabled

    def _render_loop(self):
        """Main real-time frame processing & rendering loop (~30 FPS)."""
        if not self.is_running:
            return

        start_tick = time.perf_counter()

        # 1. Read live video frame
        ret, live_frame = self.camera.read_frame()
        if not ret or live_frame is None:
            self.root.after(30, self._render_loop)
            return
        self.latest_frame = live_frame
        self.frame_count += 1

        self._process_deselect_requests()
        self._finish_selection()
        self._process_spell_commands(live_frame)

        # Auto-capture initial background baseline frame after 5 camera warm-up frames
        if self.init_frames < 5:
            self.init_frames += 1
            if self.init_frames == 5 and not self.bg_reconstructor.is_captured:
                self.bg_reconstructor.capture_background(live_frame)

        # 2. Hand & Wand Tracking
        hand_data = self.hand_tracker.process_frame(live_frame)
        self.last_hand_data = hand_data
        self._start_circle_selection(live_frame, hand_data.get("circle_bounds"))
        if hand_data.get("hand_detected"):
            wand_tip = None
        else:
            _, wand_tip = self.wand_tracker.process_frame(live_frame)

        # Add active tip position to wand light trail
        active_tip = hand_data.get("index_tip") if hand_data.get("hand_detected") else wand_tip
        if active_tip is not None:
            self.wand_trail.add_point(active_tip)

        # 3. Update Spell Controller & Physics Engine
        dt = max(0.01, start_tick - self.last_time)
        self.last_time = start_tick

        self.spell_controller.update_hand_control(hand_data)
        physics_state = self.spell_controller.update_physics(dt)

        # 4. Background Reconstruction
        orig_mask = self.spell_controller.object_mask
        orig_bbox = self.spell_controller.object_bbox
        is_detached = physics_state.get("is_detached", False)

        if is_detached and orig_mask is not None:
            # Erase original object location from live frame using reconstructed background
            reconstructed_bg = self.bg_reconstructor.reconstruct(live_frame, orig_mask, orig_bbox)
        elif self.frame_count % 30 == 0:
            # Update temporal background for static unmasked pixels
            self.bg_reconstructor.update_temporal_background(live_frame, orig_mask)
            reconstructed_bg = live_frame.copy()
        else:
            reconstructed_bg = live_frame.copy()

        # 5. Transform Floating Object
        warped_object_roi = None
        if is_detached and self.spell_controller.extracted_bgra is not None:
            center_pos = physics_state.get("center_pos", (640, 360))
            rotation_deg = physics_state.get("rotation", 0.0)
            scale = physics_state.get("scale", 1.0)

            warped_object_roi = ObjectTransformer.transform(
                extracted_bgra=self.spell_controller.extracted_bgra,
                scale=scale,
                rotation_deg=rotation_deg,
                center_pos=center_pos,
                canvas_size=(live_frame.shape[1], live_frame.shape[0])
            )

        # 6. Scene Compositing & Visual Effects
        output_frame = SceneCompositor.composite_scene(
            reconstructed_bg=reconstructed_bg,
            warped_object_roi=warped_object_roi,
            physics_state=physics_state,
            orig_mask=orig_mask,
            orig_bbox=orig_bbox,
            particle_system=self.particle_system,
            wand_trail=self.wand_trail
        )
        output_frame = self.hand_tracker.draw_circle_trace(output_frame)

        # 7. Candidate Object Highlight (when pointing or standby)
        if not is_detached:
            if orig_bbox is not None:
                output_frame = self.detector.draw_highlight(output_frame, orig_bbox)

        # 8. Render Debug Overlay (if Debug Mode is ON)
        if self.debug_mode:
            output_frame = self.hand_tracker.draw_debug(output_frame)

            # Debug Info overlay box
            cv2.rectangle(output_frame, (10, 10), (320, 140), (0, 0, 0), -1)
            cv2.rectangle(output_frame, (10, 10), (320, 140), (0, 220, 255), 1)

            cv2.putText(output_frame, "--- DEBUG METRICS ---", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)
            cv2.putText(output_frame, f"FPS: {self.camera.get_fps():.1f}", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(output_frame, f"Spell: {self.spell_controller.active_spell}", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(output_frame, f"Hand: {hand_data.get('hand_detected')} ({hand_data.get('gesture')})", (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(output_frame, f"Obj Detached: {is_detached}", (20, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(output_frame, f"Bg Captured: {self.bg_reconstructor.is_captured}", (20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # 9. Send composited frame to UI
        end_tick = time.perf_counter()
        latency_ms = (end_tick - start_tick) * 1000.0

        self.ui.update_frame(output_frame)

        obj_label = self.detector.selected_label if self.spell_controller.has_selected_object else "NONE SELECTED"
        self.ui.update_status(
            object_name=obj_label,
            spell_status=self.spell_controller.active_spell,
            hand_active=hand_data.get("hand_detected", False),
            tracking_available=self.hand_tracker.use_mediapipe,
            fps=self.camera.get_fps(),
            latency_ms=latency_ms
        )

        # Schedule next render step
        self.root.after(33, self._render_loop)

    def close(self):
        """Clean shutdown of application components."""
        self.is_running = False
        self.speech_controller.stop_listening()
        self.camera.release()
        self.selection_executor.shutdown(wait=False, cancel_futures=True)
        print("[WingardiumLeviosaApp] Shutdown cleanly.")


def main():
    root = tk.Tk()
    app = WingardiumLeviosaApp(root)

    def on_closing():
        app.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
