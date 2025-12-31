@echo off
echo 请确保已激活 rag_bot 环境
echo 如果未激活，请运行: conda activate rag_bot
echo.
echo 正在安装依赖...
pip install -r requirements.txt
echo.
echo 安装完成！现在可以运行: python main.py
pause

