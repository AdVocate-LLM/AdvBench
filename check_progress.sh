#!/bin/bash
echo "=== 问卷生成进度 ==="
echo ""

# 检查进程是否在运行
if pgrep -f "create_questionnaire.py" > /dev/null; then
    echo "✓ 脚本正在运行"
else
    echo "✗ 脚本未运行"
fi

echo ""

# 显示评分进度
echo "--- LLM评分进度 ---"
grep -oP '\[\d+/\d+\]' questionnaire_generation.log | tail -1

echo ""

# 显示最新状态
echo "--- 最新状态 ---"
tail -5 questionnaire_generation.log

echo ""

# 检查是否已生成文件夹
if [ -d "version5_for_chinsese_student_real_en_zh" ]; then
    echo "--- 已生成文件 ---"
    ls -1 version5_for_chinsese_student_real_en_zh/ | head -10
fi
