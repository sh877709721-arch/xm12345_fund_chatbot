"""
pytest配置文件
"""
import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return {
        "pool_size": 10,
        "max_overflow": 5,
        "timeout": 30,
        "recycle": 1800
    }


@pytest.fixture
def mock_redis():
    """模拟Redis连接的fixture"""
    from unittest.mock import Mock
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = "0"
    mock_redis.set.return_value = True
    mock_redis.incr.return_value = 1
    mock_redis.decr.return_value = 1
    return mock_redis