import pytest
from cool_squad.core.complexity import (
    Complexity,
    BotCharacteristics,
    ComplexityAnalysis,
    ComplexityManager
)

def test_bot_characteristics():
    # test normal values
    char = BotCharacteristics(verbosity=0.7, thoughtfulness=0.8)
    assert char.verbosity == 0.7
    assert char.thoughtfulness == 0.8
    
    # test clamping of values
    char = BotCharacteristics(verbosity=1.5, thoughtfulness=-0.1)
    assert char.verbosity == 1.0
    assert char.thoughtfulness == 0.1

def test_complexity_analysis():
    analysis = ComplexityAnalysis(
        complexity=Complexity.MEDIUM,
        requires_tools=True,
        context_tags=["question", "technical"],
        base_tokens=300
    )
    
    assert analysis.complexity == Complexity.MEDIUM
    assert analysis.requires_tools is True
    assert "question" in analysis.context_tags
    assert analysis.base_tokens == 300

def test_token_limit_calculation():
    manager = ComplexityManager()
    
    # test low complexity scaling
    analysis = ComplexityAnalysis(
        complexity=Complexity.LOW,
        requires_tools=False,
        context_tags=["greeting"],
        base_tokens=100
    )
    
    char_terse = BotCharacteristics(verbosity=0.2, thoughtfulness=0.8)
    char_verbose = BotCharacteristics(verbosity=0.9, thoughtfulness=0.8)
    
    # low complexity only scales with verbosity
    assert manager.get_token_limit(analysis, char_terse) == 20  # 100 * 0.2
    assert manager.get_token_limit(analysis, char_verbose) == 90  # 100 * 0.9
    
    # test medium/high complexity scaling
    analysis_med = ComplexityAnalysis(
        complexity=Complexity.MEDIUM,
        requires_tools=True,
        context_tags=["question"],
        base_tokens=300
    )
    
    # medium scales with both verbosity and thoughtfulness
    assert manager.get_token_limit(analysis_med, char_terse) == 108  # 300 * 0.2 * (1 + 0.8)
    assert manager.get_token_limit(analysis_med, char_verbose) == 486  # 300 * 0.9 * (1 + 0.8)

def test_thought_interval():
    manager = ComplexityManager()
    
    # test base intervals for each complexity
    low = ComplexityAnalysis(
        complexity=Complexity.LOW,
        requires_tools=False,
        context_tags=[],
        base_tokens=100
    )
    
    med = ComplexityAnalysis(
        complexity=Complexity.MEDIUM,
        requires_tools=False,
        context_tags=[],
        base_tokens=300
    )
    
    high = ComplexityAnalysis(
        complexity=Complexity.HIGH,
        requires_tools=False,
        context_tags=[],
        base_tokens=800
    )
    
    # test multiple times to account for random scatter
    for _ in range(10):
        # low complexity: ~5 mins (300s)
        interval = manager.get_thought_interval(low)
        assert 270 <= interval <= 330  # 300 ± 30s
        
        # medium complexity: ~3 mins (180s)
        interval = manager.get_thought_interval(med)
        assert 150 <= interval <= 210  # 180 ± 30s
        
        # high complexity: ~1.5 mins (90s)
        interval = manager.get_thought_interval(high)
        assert 60 <= interval <= 120  # 90 ± 30s

@pytest.mark.asyncio
async def test_message_analysis():
    manager = ComplexityManager()
    
    class MockCreate:
        async def create(self, **kwargs):
            class Response:
                class Choice:
                    class Message:
                        content = '{"complexity": "low", "requires_tools": false, "context_tags": ["greeting"]}'
                    message = Message()
                choices = [Choice()]
            return Response()
    
    class MockChat:
        def __init__(self):
            self.completions = MockCreate()
    
    class MockClient:
        def __init__(self):
            self.chat = MockChat()
    
    manager.client = MockClient()
    
    analysis = await manager.analyze_message("hey what's up")
    
    assert analysis.complexity == Complexity.LOW
    assert analysis.requires_tools is False
    assert "greeting" in analysis.context_tags
    assert analysis.base_tokens == manager.BASE_TOKENS[Complexity.LOW] 