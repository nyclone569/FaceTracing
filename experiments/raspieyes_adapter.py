"""The seam between filtered perception and interchangeable eye renderers.

Today: TrackingState -> TargetSnapshot -> baseline_intent -> RaspieyesBackend.
M4/M5: TargetSnapshot -> Attention/Character Engine -> intent -> RoboEyesBackend.
This module implements only the baseline, not social attention or RoboEyes.
"""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TargetSnapshot:
    state: str
    gaze_x: float
    gaze_y: float
    face_width: float
    updated_s: float

    @classmethod
    def from_tracking(cls, tracking):
        return cls(*tracking.get())


@dataclass(frozen=True)
class AnimationIntent:
    behavior: str
    gaze_x: float
    gaze_y: float
    face_width: float
    expression: str = "default"


def baseline_intent(target):
    """A baseline mapping, not the eventual Character State Machine."""
    return AnimationIntent("follow" if target.state == "detected" else "idle",
                           target.gaze_x, target.gaze_y, target.face_width)


class RaspieyesBackend:
    """Reuse upstream EyeLayers, EyeAnimation and render_eye; no audio capture."""

    def __init__(self, app, pygame, config):
        from types import SimpleNamespace

        self.app = app
        self.pygame = pygame
        self.config = config
        self.previous_size = app.SCREEN_SIZE
        app.SCREEN_SIZE = config["eye_size"]
        self.window_size = (config["eye_size"] * (2 if config["dual_eye"] else 1),
                            config["eye_size"])
        pygame.display.init()
        self.screen = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("FaceTracing — Raspieyes baseline")
        self.layers = app.EyeLayers(config["eye_color"])
        self.animation = app.EyeAnimation()
        self.render_args = SimpleNamespace(
            sclera_parallax=app.DEFAULT_SCLERA_PARALLAX,
            iris_parallax=app.DEFAULT_IRIS_PARALLAX,
            pupil_parallax=app.DEFAULT_PUPIL_PARALLAX,
            max_offset=app.DEFAULT_MAX_OFFSET * config["eye_size"] / self.previous_size,
        )

    def render(self, intent, dt):
        self.animation.update("detected" if intent.behavior == "follow" else "idle",
                              intent.gaze_x, intent.gaze_y, min(dt, 0.1),
                              face_w=intent.face_width, audio=None)
        size = self.config["eye_size"]
        if self.config["dual_eye"]:
            left = self.screen.subsurface((0, 0, size, size))
            right = self.screen.subsurface((size, 0, size, size))
            self.app.render_eye(left, self.layers, self.animation, self.render_args, True)
            self.app.render_eye(right, self.layers, self.animation, self.render_args, False)
        else:
            self.app.render_eye(self.screen, self.layers, self.animation, self.render_args, True)
        self.pygame.display.flip()

    def close(self):
        self.pygame.display.quit()
        self.app.SCREEN_SIZE = self.previous_size


def intent_record(intent):
    return asdict(intent)
