"""
Модуль правил для генератора стохастической речи
"""

from .base import Rule
from .acoustic import (
    PitchProximityRule,
    PitchDirectionRule,
    DurationPatternRule,
    AmplitudeWaveRule,
    MFCCProximityRule
)
from .emotional import (
    EmotionWaveRule,
    EmotionContrastRule,
    SentimentGradientRule
)
from .phonetic import (
    AlliterationRule,
    VowelConsonantRatioRule,
    VoicingAlternationRule
)
from .grammatical import (
    POSPatternRule,
    POSAlternationRule
)

__all__ = [
    'Rule',
    # Acoustic
    'PitchProximityRule',
    'PitchDirectionRule', 
    'DurationPatternRule',
    'AmplitudeWaveRule',
    'MFCCProximityRule',
    # Emotional
    'EmotionWaveRule',
    'EmotionContrastRule',
    'SentimentGradientRule',
    # Phonetic
    'AlliterationRule',
    'VowelConsonantRatioRule',
    'VoicingAlternationRule',
    # Grammatical
    'POSPatternRule',
    'POSAlternationRule'
]
