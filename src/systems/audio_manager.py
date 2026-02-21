"""
Audio Manager - Procedural sound generation for Temporal Debt.

Generates all sounds programmatically using pygame and numpy.
No external audio files required!

Features:
- Procedurally generated sound effects
- Dynamic music that responds to game state
- Volume control and mixing
"""

import pygame
import numpy as np
import math
from typing import Dict, Optional
from enum import Enum, auto

from ..core.settings import Settings


class SoundType(Enum):
    """Types of sounds in the game."""
    # Core mechanics
    TIME_FREEZE_START = auto()
    TIME_FREEZE_LOOP = auto()
    TIME_FREEZE_END = auto()
    DEBT_TICK = auto()
    DEBT_WARNING = auto()
    DEBT_CRITICAL = auto()
    
    # Player actions
    PLAYER_DEATH = auto()
    ANCHOR_PLACE = auto()
    ANCHOR_RECALL = auto()
    
    # V2.0 Features
    FRAGMENT_COLLECT = auto()
    FRAGMENT_BURST = auto()
    CLONE_SPAWN = auto()
    CLONE_DESPAWN = auto()
    REWIND_ACTIVATE = auto()
    RESONANCE_WARNING = auto()
    RESONANCE_WAVE = auto()
    POD_DEPOSIT = auto()
    
    # UI
    LEVEL_COMPLETE = auto()
    MENU_SELECT = auto()
    MENU_CONFIRM = auto()


class ProceduralSoundGenerator:
    """Generates sounds using mathematical waveforms."""
    
    SAMPLE_RATE = 44100
    
    @staticmethod
    def generate_sine_wave(frequency: float, duration: float, 
                          volume: float = 0.5, fade_out: bool = True) -> np.ndarray:
        """Generate a pure sine wave tone."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, False)
        wave = np.sin(2 * np.pi * frequency * t) * volume
        
        if fade_out:
            # Apply exponential fade out
            fade = np.exp(-t * 3 / duration)
            wave = wave * fade
        
        # Convert to 16-bit stereo
        wave = (wave * 32767).astype(np.int16)
        stereo = np.column_stack((wave, wave))
        return stereo
    
    @staticmethod
    def generate_sweep(start_freq: float, end_freq: float, duration: float,
                      volume: float = 0.5, wave_type: str = 'sine') -> np.ndarray:
        """Generate a frequency sweep (ascending or descending)."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        # Exponential frequency sweep
        freq = start_freq * (end_freq / start_freq) ** (t / duration)
        phase = 2 * np.pi * np.cumsum(freq) / ProceduralSoundGenerator.SAMPLE_RATE
        
        if wave_type == 'sine':
            wave = np.sin(phase)
        elif wave_type == 'square':
            wave = np.sign(np.sin(phase))
        else:
            wave = np.sin(phase)
        
        wave = wave * volume
        
        # Fade out
        fade = np.exp(-t * 2 / duration)
        wave = wave * fade
        
        wave = (wave * 32767).astype(np.int16)
        return np.column_stack((wave, wave))
    
    @staticmethod
    def generate_noise_burst(duration: float, volume: float = 0.3,
                            filter_type: str = 'white') -> np.ndarray:
        """Generate filtered noise."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        
        # White noise
        noise = np.random.uniform(-1, 1, num_samples)
        
        if filter_type == 'pink':
            # Simple low-pass filter for pink-ish noise
            b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
            a = [1, -2.494956002, 2.017265875, -0.522189400]
            from scipy import signal
            try:
                noise = signal.lfilter(b, a, noise)
            except:
                pass  # Fall back to white noise
        
        # Apply envelope
        t = np.linspace(0, duration, num_samples, False)
        envelope = np.exp(-t * 5 / duration)
        noise = noise * envelope * volume
        
        noise = (noise * 32767).astype(np.int16)
        return np.column_stack((noise, noise))
    
    @staticmethod
    def generate_blip(frequency: float, duration: float = 0.1,
                     volume: float = 0.4) -> np.ndarray:
        """Generate a short blip/beep sound."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        # Quick attack, quick decay
        envelope = np.sin(np.pi * t / duration)
        wave = np.sin(2 * np.pi * frequency * t) * envelope * volume
        
        wave = (wave * 32767).astype(np.int16)
        return np.column_stack((wave, wave))
    
    @staticmethod
    def generate_chime(base_freq: float, duration: float = 0.5,
                      volume: float = 0.4) -> np.ndarray:
        """Generate a pleasant chime with harmonics."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        # Multiple harmonics for rich sound
        wave = np.zeros(num_samples)
        harmonics = [1, 2, 3, 4, 5]
        amplitudes = [1.0, 0.5, 0.25, 0.125, 0.0625]
        
        for h, amp in zip(harmonics, amplitudes):
            wave += np.sin(2 * np.pi * base_freq * h * t) * amp
        
        # Normalize
        wave = wave / np.max(np.abs(wave))
        
        # Bell-like envelope (quick attack, slow decay)
        envelope = np.exp(-t * 4 / duration)
        wave = wave * envelope * volume
        
        wave = (wave * 32767).astype(np.int16)
        return np.column_stack((wave, wave))
    
    @staticmethod
    def generate_alarm(frequency: float, duration: float = 0.5,
                      pulses: int = 3, volume: float = 0.5) -> np.ndarray:
        """Generate an alarm/warning sound."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        # Pulsing envelope
        pulse_freq = pulses / duration
        envelope = (np.sin(2 * np.pi * pulse_freq * t) + 1) / 2
        
        # Two-tone alarm
        wave1 = np.sin(2 * np.pi * frequency * t)
        wave2 = np.sin(2 * np.pi * frequency * 1.2 * t)
        
        # Alternate between tones
        selector = np.sin(2 * np.pi * pulse_freq * 2 * t) > 0
        wave = np.where(selector, wave1, wave2)
        
        wave = wave * envelope * volume
        
        # Fade out at end
        fade_samples = int(num_samples * 0.1)
        wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        wave = (wave * 32767).astype(np.int16)
        return np.column_stack((wave, wave))
    
    @staticmethod
    def generate_whoosh(duration: float = 0.3, volume: float = 0.4,
                       direction: str = 'up') -> np.ndarray:
        """Generate a whoosh/swoosh sound."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        # Filtered noise with frequency modulation
        noise = np.random.uniform(-1, 1, num_samples)
        
        # Frequency envelope
        if direction == 'up':
            freq_mult = np.linspace(0.2, 1.0, num_samples)
        else:
            freq_mult = np.linspace(1.0, 0.2, num_samples)
        
        # Simple low-pass by averaging
        kernel_size = 10
        kernel = np.ones(kernel_size) / kernel_size
        noise = np.convolve(noise, kernel, mode='same')
        
        # Amplitude envelope
        envelope = np.sin(np.pi * t / duration) * volume
        
        wave = noise * envelope * freq_mult
        wave = (wave * 32767).astype(np.int16)
        return np.column_stack((wave, wave))
    
    @staticmethod
    def generate_rewind(duration: float = 0.8, volume: float = 0.5) -> np.ndarray:
        """Generate a tape rewind effect."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        # Multiple descending tones
        wave = np.zeros(num_samples)
        
        for i in range(5):
            freq_start = 2000 - i * 300
            freq_end = 100 + i * 50
            freq = freq_start * (freq_end / freq_start) ** (t / duration)
            phase = 2 * np.pi * np.cumsum(freq) / ProceduralSoundGenerator.SAMPLE_RATE
            wave += np.sin(phase) * (0.3 ** i)
        
        # Add some noise texture
        noise = np.random.uniform(-0.2, 0.2, num_samples)
        wave = wave + noise
        
        # Normalize and apply envelope
        wave = wave / np.max(np.abs(wave))
        envelope = 1 - (t / duration) ** 2  # Quick start, slow fade
        wave = wave * envelope * volume
        
        wave = (wave * 32767).astype(np.int16)
        return np.column_stack((wave, wave))
    
    @staticmethod
    def generate_power_up(duration: float = 0.6, volume: float = 0.5) -> np.ndarray:
        """Generate a power-up/burst sound."""
        num_samples = int(ProceduralSoundGenerator.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        # Rising frequency
        freq = 200 + 800 * (t / duration) ** 2
        phase = 2 * np.pi * np.cumsum(freq) / ProceduralSoundGenerator.SAMPLE_RATE
        wave = np.sin(phase)
        
        # Add harmonics
        wave += np.sin(phase * 2) * 0.5
        wave += np.sin(phase * 3) * 0.25
        
        # Bright burst envelope
        envelope = np.sin(np.pi * t / duration) ** 0.5
        wave = wave * envelope * volume / 1.75
        
        wave = (wave * 32767).astype(np.int16)
        return np.column_stack((wave, wave))


class AudioManager:
    """
    Manages all game audio including procedural generation.
    
    Usage:
        audio = AudioManager()
        audio.play(SoundType.TIME_FREEZE_START)
    """
    
    def __init__(self):
        """Initialize the audio manager."""
        self._initialized = False
        self._sounds: Dict[SoundType, pygame.mixer.Sound] = {}
        self._channels: Dict[str, pygame.mixer.Channel] = {}
        
        # Volume settings
        self._master_volume = 0.7
        self._sfx_volume = 0.8
        self._music_volume = 0.5
        
        # Music state
        self._current_music: Optional[pygame.mixer.Sound] = None
        self._music_channel: Optional[pygame.mixer.Channel] = None
        
        # Initialize
        self._init_audio()
    
    def _init_audio(self) -> None:
        """Initialize pygame audio and generate all sounds."""
        try:
            # Initialize mixer with good settings
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            
            # Reserve channels
            self._channels['music'] = pygame.mixer.Channel(0)
            self._channels['ambience'] = pygame.mixer.Channel(1)
            self._channels['effects'] = pygame.mixer.Channel(2)
            
            # Generate all sounds
            self._generate_all_sounds()
            
            self._initialized = True
            print("Audio system initialized with procedural sounds!")
            
        except Exception as e:
            print(f"Audio initialization failed: {e}")
            self._initialized = False
    
    def _generate_all_sounds(self) -> None:
        """Generate all game sounds procedurally."""
        gen = ProceduralSoundGenerator
        
        # Core mechanics
        self._sounds[SoundType.TIME_FREEZE_START] = self._create_sound(
            gen.generate_sweep(800, 200, 0.3, 0.5)
        )
        self._sounds[SoundType.TIME_FREEZE_LOOP] = self._create_sound(
            gen.generate_sine_wave(80, 2.0, 0.2, fade_out=False)
        )
        self._sounds[SoundType.TIME_FREEZE_END] = self._create_sound(
            gen.generate_sweep(200, 800, 0.25, 0.5)
        )
        self._sounds[SoundType.DEBT_TICK] = self._create_sound(
            gen.generate_blip(440, 0.05, 0.15)
        )
        self._sounds[SoundType.DEBT_WARNING] = self._create_sound(
            gen.generate_alarm(600, 0.4, 2, 0.4)
        )
        self._sounds[SoundType.DEBT_CRITICAL] = self._create_sound(
            gen.generate_alarm(800, 0.5, 4, 0.5)
        )
        
        # Player actions
        self._sounds[SoundType.PLAYER_DEATH] = self._create_sound(
            gen.generate_sweep(400, 50, 0.8, 0.6)
        )
        self._sounds[SoundType.ANCHOR_PLACE] = self._create_sound(
            gen.generate_chime(880, 0.4, 0.5)
        )
        self._sounds[SoundType.ANCHOR_RECALL] = self._create_sound(
            gen.generate_sweep(440, 880, 0.3, 0.5)
        )
        
        # V2.0 Features
        self._sounds[SoundType.FRAGMENT_COLLECT] = self._create_sound(
            gen.generate_chime(1200, 0.3, 0.5)
        )
        self._sounds[SoundType.FRAGMENT_BURST] = self._create_sound(
            gen.generate_power_up(0.6, 0.6)
        )
        self._sounds[SoundType.CLONE_SPAWN] = self._create_sound(
            gen.generate_whoosh(0.3, 0.4, 'up')
        )
        self._sounds[SoundType.CLONE_DESPAWN] = self._create_sound(
            gen.generate_whoosh(0.3, 0.3, 'down')
        )
        self._sounds[SoundType.REWIND_ACTIVATE] = self._create_sound(
            gen.generate_rewind(0.8, 0.5)
        )
        self._sounds[SoundType.RESONANCE_WARNING] = self._create_sound(
            gen.generate_sweep(200, 600, 1.0, 0.4)
        )
        self._sounds[SoundType.RESONANCE_WAVE] = self._create_sound(
            gen.generate_whoosh(0.5, 0.5, 'up')
        )
        self._sounds[SoundType.POD_DEPOSIT] = self._create_sound(
            gen.generate_blip(330, 0.15, 0.3)
        )
        
        # UI
        self._sounds[SoundType.LEVEL_COMPLETE] = self._create_sound(
            self._generate_victory_fanfare()
        )
        self._sounds[SoundType.MENU_SELECT] = self._create_sound(
            gen.generate_blip(660, 0.08, 0.3)
        )
        self._sounds[SoundType.MENU_CONFIRM] = self._create_sound(
            gen.generate_chime(880, 0.2, 0.4)
        )
    
    def _generate_victory_fanfare(self) -> np.ndarray:
        """Generate a victory fanfare."""
        gen = ProceduralSoundGenerator
        
        # Three ascending notes
        note1 = gen.generate_chime(523, 0.2, 0.4)  # C
        note2 = gen.generate_chime(659, 0.2, 0.4)  # E
        note3 = gen.generate_chime(784, 0.4, 0.5)  # G
        
        # Concatenate with small gaps
        gap = np.zeros((int(44100 * 0.05), 2), dtype=np.int16)
        
        result = np.concatenate([note1, gap, note2, gap, note3])
        return result
    
    def _create_sound(self, samples: np.ndarray) -> pygame.mixer.Sound:
        """Create a pygame Sound from numpy array."""
        return pygame.mixer.Sound(buffer=samples.tobytes())
    
    def play(self, sound_type: SoundType, volume: float = 1.0, loop: bool = False) -> None:
        """
        Play a sound effect.
        
        Args:
            sound_type: Type of sound to play
            volume: Volume multiplier (0.0 - 1.0)
            loop: Whether to loop the sound
        """
        if not self._initialized:
            return
        
        if sound_type not in self._sounds:
            return
        
        sound = self._sounds[sound_type]
        sound.set_volume(self._master_volume * self._sfx_volume * volume)
        
        loops = -1 if loop else 0
        sound.play(loops=loops)
    
    def stop(self, sound_type: SoundType) -> None:
        """Stop a specific sound."""
        if not self._initialized:
            return
        
        if sound_type in self._sounds:
            self._sounds[sound_type].stop()
    
    def stop_all(self) -> None:
        """Stop all sounds."""
        if self._initialized:
            pygame.mixer.stop()
    
    def set_master_volume(self, volume: float) -> None:
        """Set master volume (0.0 - 1.0)."""
        self._master_volume = max(0.0, min(1.0, volume))
    
    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume (0.0 - 1.0)."""
        self._sfx_volume = max(0.0, min(1.0, volume))
    
    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 - 1.0)."""
        self._music_volume = max(0.0, min(1.0, volume))
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        if self._initialized:
            self.stop_all()
            pygame.mixer.quit()


# Global audio manager instance
_audio_manager: Optional[AudioManager] = None


def get_audio_manager() -> AudioManager:
    """Get or create the global audio manager."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager


def play_sound(sound_type: SoundType, volume: float = 1.0) -> None:
    """Convenience function to play a sound."""
    get_audio_manager().play(sound_type, volume)
