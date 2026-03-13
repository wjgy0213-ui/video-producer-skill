#!/usr/bin/env python3
"""
SkillPay 计费集成层 v1.0
基于 SkillPay.me 的 /billing/charge API

配置：
  环境变量 SKILLPAY_API_KEY 或 config.json 中 skillpay_api_key
  
用法：
  from skillpay import charge, create_billing_wrapper

  # 方式1：手动检查
  result = charge(user_id="user123", amount=1.0)
  if result["success"]:
      # 执行 Skill 逻辑
  else:
      # 返回 result["payment_url"] 让用户充值

  # 方式2：装饰器自动包装
  @create_billing_wrapper(amount=1.0)
  def my_skill(input_data):
      return {"result": "..."}
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from functools import wraps

SKILLPAY_BASE_URL = os.environ.get("SKILLPAY_BASE_URL", "https://skillpay.me/api/v1/billing")
CONFIG_PATH = Path(__file__).parent / "config.json"


def _get_api_key() -> str:
    """获取 API Key（环境变量优先，其次 config.json）"""
    key = os.environ.get("SKILLPAY_API_KEY")
    if key:
        return key
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text())
        return config.get("skillpay_api_key", "")
    return ""


def _get_skill_id() -> str:
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text())
        return config.get("skill_id", "")
    return ""


def charge(user_id: str, amount: float = 1.0, skill_id: str = None,
           description: str = "PREP Content Generation") -> dict:
    """
    向用户收费
    
    Args:
        user_id: 用户标识（SkillPay user ID）
        amount: 收费金额（token单位）
        skill_id: Skill 标识
        description: 收费描述
    
    Returns:
        {"success": True} 或 {"success": False, "payment_url": "https://...", "message": "..."}
    """
    api_key = _get_api_key()
    if not api_key:
        # 没有 API key = 免费模式（开发/测试用）
        return {"success": True, "mode": "free", "message": "No SkillPay API key configured, running in free mode"}
    
    if not skill_id:
        skill_id = _get_skill_id()
    
    payload = json.dumps({
        "user_id": user_id,
        "skill_id": skill_id,
        "amount": 0,  # SkillPay deducts 1 token per call automatically
    }).encode()
    
    req = urllib.request.Request(
        f"{SKILLPAY_BASE_URL}/charge",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return {"success": True, "data": data}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.readable() else ""
        try:
            error_data = json.loads(body)
        except json.JSONDecodeError:
            error_data = {"raw": body}
        
        if e.code == 402:
            # 余额不足 → 返回充值链接
            return {
                "success": False,
                "payment_url": error_data.get("payment_url", f"https://skillpay.me/pay/{skill_id}"),
                "message": error_data.get("message", "Insufficient balance. Please top up."),
            }
        return {
            "success": False,
            "error": f"HTTP {e.code}",
            "message": error_data.get("message", body),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "message": "SkillPay connection failed"}


def create_billing_wrapper(amount: float = 1.0, skill_id: str = "prep-content"):
    """
    装饰器：自动在 Skill 执行前收费
    
    用法:
        @create_billing_wrapper(amount=1.0)
        def generate_content(input_data):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(input_data, *args, **kwargs):
            user_id = input_data.get("user_id", "anonymous")
            
            # 收费
            billing_result = charge(
                user_id=user_id,
                amount=amount,
                skill_id=skill_id,
                description=f"PREP {input_data.get('action', 'generate')}",
            )
            
            if not billing_result["success"]:
                return {
                    "error": "payment_required",
                    "payment_url": billing_result.get("payment_url"),
                    "message": billing_result.get("message"),
                }
            
            # 执行 Skill
            result = func(input_data, *args, **kwargs)
            result["billing"] = {"charged": True, "amount": amount, "mode": billing_result.get("mode", "paid")}
            return result
        
        return wrapper
    return decorator


# ============================================================
# 配置管理
# ============================================================

def setup(api_key: str = None, wallet: str = None):
    """初始化 SkillPay 配置"""
    config = {}
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text())
    
    if api_key:
        config["skillpay_api_key"] = api_key
    if wallet:
        config["skillpay_wallet"] = wallet
    
    config["skill_id"] = "prep-content"
    config["skill_name"] = "PREP Content Creator"
    config["version"] = "2.0.0"
    config["pricing"] = {
        "generate": 1.0,
        "analyze": 0.5,
        "examples": 0.0,  # 免费
        "types": 0.0,
        "platforms": 0.0,
        "sensitive_check": 0.0,
    }
    
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    return config


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        api_key = sys.argv[2] if len(sys.argv) > 2 else input("SkillPay API Key: ")
        wallet = sys.argv[3] if len(sys.argv) > 3 else input("BSC Wallet Address: ")
        config = setup(api_key, wallet)
        print(f"✅ Config saved to {CONFIG_PATH}")
        print(json.dumps(config, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        result = charge("test_user", 0.0, "prep-content", "Test charge")
        print(json.dumps(result, indent=2))
    else:
        print("Usage:")
        print("  python3 skillpay.py setup [api_key] [wallet]")
        print("  python3 skillpay.py test")
