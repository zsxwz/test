import os
import re
import asyncio
import shutil
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Environment settings
ROOT_PATH = "/root"
os.environ['HOME'] = ROOT_PATH
HOME_PATH = ROOT_PATH

# Load environment variables from .env file
load_dotenv()

# Bot configuration from .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Global variables
tasks = []
task_counter = 0
task_chat_map = {}

# Ensure necessary directories exist
os.makedirs(f"{HOME_PATH}/tdlbot/download", exist_ok=True)
os.makedirs(f"{HOME_PATH}/tdlbot/upload", exist_ok=True)
os.makedirs(f"{HOME_PATH}/tdlbot/fonts", exist_ok=True)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("你好。")


async def fw_to_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global task_counter
    message = update.message.text
    pattern = r'/fw_to_reply (\S+) (\d+) (\d+) (\S+) (\d+)'
    match = re.match(pattern, message)

    if match:
        s_name, s_num, e_num, t_name, r_num = match.groups()
        task_counter += 1
        task_id = task_counter
        task = ("fw_to_reply", task_id, s_name, s_num, e_num, t_name, r_num)
        tasks.append(task)
        task_chat_map[task_id] = update.effective_chat.id
        await update.message.reply_text(f"任务已添加到队列。任务ID: {task_id}，源频道：{s_name}，开始下载：{s_num}，结束下载：{e_num}，目标频道：{t_name}")

        if len(tasks) == 1:
            asyncio.create_task(task_processor(context))
    else:
        await update.message.reply_text("命令格式错误。请使用：/fw_to_reply <源频道用户名> <开始消息id> <结束消息id> <目标频道用户名> <评论消息id>")


async def fw_to_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global task_counter
    message = update.message.text
    pattern = r'/fw_to_topic (\S+) (\d+) (\d+) (\S+) (\d+)'
    match = re.match(pattern, message)

    if match:
        s_name, s_num, e_num, t_name, t_topic_id = match.groups()
        task_counter += 1
        task_id = task_counter
        task = ("fw_to_topic", task_id, s_name, s_num, e_num, t_name, t_topic_id)
        tasks.append(task)
        task_chat_map[task_id] = update.effective_chat.id
        await update.message.reply_text(f"任务已添加到队列。任务ID: {task_id}，源频道：{s_name}，开始下载：{s_num}，结束下载：{e_num}，目标群组：{t_name}，目标群组分组id：{t_topic_id}")

        if len(tasks) == 1:
            asyncio.create_task(task_processor(context))
    else:
        await update.message.reply_text("命令格式错误。请使用：/fw_to_topic <源频道用户名> <开始消息id> <结束消息id> <目标群组用户名> <目标群组分组id>")


async def fw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global task_counter
    message = update.message.text
    pattern = r'/fw (\S+) (\d+) (\d+) (\S+)'
    match = re.match(pattern, message)

    if match:
        s_name, s_num, e_num, t_name = match.groups()
        task_counter += 1
        task_id = task_counter
        task = ("fw", task_id, s_name, s_num, e_num, t_name)
        tasks.append(task)
        task_chat_map[task_id] = update.effective_chat.id
        await update.message.reply_text(f"任务已添加到队列。任务ID: {task_id}，源频道：{s_name}，开始下载：{s_num}，结束下载：{e_num}，目标频道：{t_name}")

        if len(tasks) == 1:
            asyncio.create_task(task_processor(context))
    else:
        await update.message.reply_text("命令格式错误。请使用：/fw <源频道用户名> <开始消息id> <结束消息id> <目标频道用户名>")


async def topic_to_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global task_counter
    message = update.message.text
    pattern = r'/topic_to_topic (\S+) (\d+) (\S+) (\d+)'
    match = re.match(pattern, message)

    if match:
        s_name, s_topic_id, t_name, t_topic_id = match.groups()
        task_counter += 1
        task_id = task_counter
        task = ("topic_to_topic", task_id, s_name, s_topic_id, t_name, t_topic_id)
        tasks.append(task)
        task_chat_map[task_id] = update.effective_chat.id
        await update.message.reply_text(f"任务已添加到队列。任务ID: {task_id}，原群组：{s_name}，原群组分组id：{s_topic_id}，目标群组：{t_name}，目标群组分组id：{t_topic_id}")

        if len(tasks) == 1:
            asyncio.create_task(task_processor(context))
    else:
        await update.message.reply_text("命令格式错误。请使用：/topic_to_topic <原群组用户名> <原群组分组id> <目标群组用户名> <目标群组分组id>")


async def reply_to_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global task_counter
    message = update.message.text
    pattern = r'/reply_to_reply (\S+) (\d+) (\S+) (\d+)'
    match = re.match(pattern, message)

    if match:
        s_name, s_reply_id, t_name, t_reply_id = match.groups()
        task_counter += 1
        task_id = task_counter
        task = ("reply_to_reply", task_id, s_name, s_reply_id, t_name, t_reply_id)
        tasks.append(task)
        task_chat_map[task_id] = update.effective_chat.id
        await update.message.reply_text(f"任务已添加到队列。任务ID: {task_id}，原频道：{s_name}，原频道评论id：{s_reply_id}，目标频道：{t_name}，目标频道评论id：{t_reply_id}")

        if len(tasks) == 1:
            asyncio.create_task(task_processor(context))
    else:
        await update.message.reply_text("命令格式错误。请使用：/reply_to_reply <原频道用户名> <原频道评论id> <目标频道用户名> <目标频道评论id>")


# Task execution functions
async def execute_fw_to_reply_task(task, context: ContextTypes.DEFAULT_TYPE):
    _, task_id, s_name, s_num, e_num, t_name, r_num = task

    # Download export
    os.system(f'tdl -n lks chat export -c {s_name} -T id -i {s_num},{e_num} -o output_{task_id}.json')

    # Upload to target channel
    os.system(f'tdl -n lks forward -t 8 --pool 8 -s 524288 --reconnect-timeout 0 --from output_{task_id}.json --edit edit.txt --to \'{{ Peer: "{t_name}", Thread: {r_num} }}\' --mode clone --desc')

    # Clean up temporary files
    os.remove(f'output_{task_id}.json')

    # Send completion notification
    chat_id = task_chat_map.pop(task_id, None)
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=f"任务ID: {task_id} 的上传已完成。")


async def execute_fw_to_topic_task(task, context: ContextTypes.DEFAULT_TYPE):
    _, task_id, s_name, s_num, e_num, t_name, t_topic_id = task

    # Download export
    os.system(f'tdl -n lks chat export -c {s_name} -T id -i {s_num},{e_num} -o output_{task_id}.json')

    # Upload to target channel
    os.system(f'tdl -n lks forward -t 8 --pool 8 -s 524288 --reconnect-timeout 0 --from output_{task_id}.json --edit edit.txt --to \'{{ Peer: "{t_name}", Thread: {t_topic_id} }}\' --mode clone --desc')

    # Clean up temporary files
    os.remove(f'output_{task_id}.json')

    # Send completion notification
    chat_id = task_chat_map.pop(task_id, None)
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=f"任务ID: {task_id} 的上传已完成。")


async def execute_fw_task(task, context: ContextTypes.DEFAULT_TYPE):
    _, task_id, s_name, s_num, e_num, t_name = task

    # Download export
    os.system(f'tdl -n lks chat export -c {s_name} -T id -i {s_num},{e_num} -o output_{task_id}.json')

    # Upload to target channel
    os.system(f'tdl -n lks forward -t 8 --pool 8 -s 524288 --reconnect-timeout 0 --from output_{task_id}.json --edit edit.txt --to {t_name} --mode clone --desc')

    # Clean up temporary files
    os.remove(f'output_{task_id}.json')

    # Send completion notification
    chat_id = task_chat_map.pop(task_id, None)
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=f"任务ID: {task_id} 的上传已完成。")


async def execute_topic_to_topic_task(task, context: ContextTypes.DEFAULT_TYPE):
    _, task_id, s_name, s_topic_id, t_name, t_topic_id = task

    # Download export
    os.system(f'tdl -n lks chat export -c {s_name} --topic {s_topic_id} -o output_{task_id}.json')

    # Upload to target channel
    os.system(f'tdl -n lks forward -t 8 --pool 8 -s 524288 --reconnect-timeout 0 --from output_{task_id}.json --edit edit.txt --to \'{{ Peer: "{t_name}", Thread: {t_topic_id} }}\' --mode clone --desc')

    # Clean up temporary files
    os.remove(f'output_{task_id}.json')

    # Send completion notification
    chat_id = task_chat_map.pop(task_id, None)
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=f"任务ID: {task_id} 的上传已完成。")


async def execute_reply_to_reply_task(task, context: ContextTypes.DEFAULT_TYPE):
    _, task_id, s_name, s_reply_id, t_name, t_reply_id = task

    # Download export
    os.system(f'tdl -n lks chat export -c {s_name} --reply {s_reply_id} -o output_{task_id}.json')

    # Upload to target channel
    os.system(f'tdl -n lks forward -t 8 --pool 8 -s 524288 --reconnect-timeout 0 --from output_{task_id}.json --edit edit.txt --to \'{{ Peer: "{t_name}", Thread: {t_reply_id} }}\' --mode clone --desc')

    # Clean up temporary files
    os.remove(f'output_{task_id}.json')

    # Send completion notification
    chat_id = task_chat_map.pop(task_id, None)
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=f"任务ID: {task_id} 的上传已完成。")


async def task_processor(context: ContextTypes.DEFAULT_TYPE):
    while tasks:
        task = tasks.pop(0)
        task_type = task[0]
        
        if task_type == "fw_to_reply":
            await execute_fw_to_reply_task(task, context)
        elif task_type == "fw":
            await execute_fw_task(task, context)
        elif task_type == "topic_to_topic":
            await execute_topic_to_topic_task(task, context)
        elif task_type == "reply_to_reply":
            await execute_reply_to_reply_task(task, context)
        elif task_type == "fw_to_topic":
            await execute_fw_to_topic_task(task, context)
        elif task_type == "fw_mark":
            await execute_fw_mark_task(task, context)

# Now import the mark module AFTER defining task_processor
from mark import init_mark_command, execute_fw_mark_task

# Initialize fw_mark command handler
fw_mark = init_mark_command(tasks, task_counter, task_chat_map, task_processor)

# Main function
def main():
    # Initialize the application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("fw_to_reply", fw_to_reply))
    application.add_handler(CommandHandler("fw", fw))
    application.add_handler(CommandHandler("topic_to_topic", topic_to_topic))
    application.add_handler(CommandHandler("reply_to_reply", reply_to_reply))
    application.add_handler(CommandHandler("fw_to_topic", fw_to_topic))
    application.add_handler(CommandHandler("fw_mark", fw_mark))

    # Start the Bot
    application.run_polling()


if __name__ == '__main__':
    main()
