#!/usr/bin/env python3
"""
测试运行脚本
运行项目的所有测试并生成报告
"""

import subprocess
import sys
import os


def run_command(command, description):
    """运行命令并打印结果"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
        else:
            print(f"❌ {description} - 失败 (退出码: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 运行 {description} 时出错: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始运行 AI Talk 项目测试套件")
    
    # 检查是否安装了pytest
    if not run_command("python -m pytest --version", "检查 pytest 是否安装"):
        print("\n❌ pytest 未安装，请先安装依赖:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    success_count = 0
    total_tests = 0
    
    # 运行不同类型的测试
    test_commands = [
        {
            "command": "python -m pytest tests/test_api.py -v",
            "description": "API 集成测试"
        },
        {
            "command": "python -m pytest tests/test_services.py -v",
            "description": "服务层单元测试"
        },
        {
            "command": "python -m pytest tests/test_security.py -v",
            "description": "安全性测试"
        },
        {
            "command": "python -m pytest tests/ -v --tb=short",
            "description": "所有测试（简要输出）"
        },
        {
            "command": "python -m pytest tests/ --cov=app --cov-report=term-missing",
            "description": "测试覆盖率报告"
        }
    ]
    
    for test in test_commands:
        total_tests += 1
        if run_command(test["command"], test["description"]):
            success_count += 1
    
    # 生成测试报告
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    print(f"总测试套件: {total_tests}")
    print(f"成功: {success_count}")
    print(f"失败: {total_tests - success_count}")
    print(f"成功率: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 所有测试都通过了！")
        return 0
    else:
        print(f"\n⚠️  有 {total_tests - success_count} 个测试套件失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 