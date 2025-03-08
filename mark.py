import os
import re
import json
import shutil
import asyncio
import time
from dotenv import load_dotenv
from telethon import TelegramClient
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

# Environment settings
ROOT_PATH = "/root"
HOME_PATH = ROOT_PATH

# Load environment variables from .env file
load_dotenv()

# Get configuration from .env
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Watermark settings from .env
WATERMARK_TEXT = os.getenv("WATERMARK_TEXT")
WATERMARK_FONTSIZE = int(os.getenv("WATERMARK_FONTSIZE", "24"))
WATERMARK_COLOR = os.getenv("WATERMARK_COLOR")
WATERMARK_POSITION_X = os.getenv("WATERMARK_POSITION_X")
WATERMARK_POSITION_Y = os.getenv("WATERMARK_POSITION_Y")
WATERMARK_FONT = f"{HOME_PATH}/tdlbot/{os.getenv('WATERMARK_FONT')}"

# Initialize Telethon client
client = TelegramClient('mark_session', API_ID, API_HASH)
client.start()
print("Telethon client initialized and authenticated")

# Progress tracking
last_progress_update = {}


def init_mark_command(tasks, task_counter, task_chat_map, task_processor):
    """Initialize fw_mark command handler"""
    
    async def fw_mark(update: Update, context: ContextTypes.DEFAULT_TYPE):
        nonlocal tasks, task_counter
        message = update.message.text
        pattern = r'/fw_mark (\S+) (\d+) (\d+) (\S+)'
        match = re.match(pattern, message)

        if match:
            s_name, s_num, e_num, t_name = match.groups()
            task_counter += 1
            task_id = task_counter
            task = ("fw_mark", task_id, s_name, s_num, e_num, t_name)
            tasks.append(task)
            task_chat_map[task_id] = update.effective_chat.id
            await update.message.reply_text(f"任务已添加到队列。任务ID: {task_id}，源频道：{s_name}，开始下载：{s_num}，结束下载：{e_num}，目标频道：{t_name}")

            if len(tasks) == 1:
                asyncio.create_task(task_processor(context))
        else:
            await update.message.reply_text("命令格式错误。请使用：/fw_mark <源频道用户名> <开始消息id> <结束消息id> <目标频道用户名>")
    
    return fw_mark


async def upload_progress_callback(current, total, start_time, message_id, chat_id, context):
    """Callback for upload progress reporting"""
    global last_progress_update
    
    # Update progress at most once per second to avoid spam
    current_time = time.time()
    if message_id in last_progress_update and current_time - last_progress_update[message_id] < 1:
        return
    
    last_progress_update[message_id] = current_time
    
    # Calculate percentage and speed
    percentage = round((current / total) * 100, 1)
    elapsed = current_time - start_time
    speed = current / elapsed if elapsed > 0 else 0  # bytes per second
    
    # Convert to appropriate units
    if speed < 1024:
        speed_str = f"{speed:.2f} B/s"
    elif speed < 1024 * 1024:
        speed_str = f"{speed/1024:.2f} KB/s"
    else:
        speed_str = f"{speed/(1024*1024):.2f} MB/s"
    
    # Update progress message
    try:
        progress_text = f"上传进度: {percentage}% ({speed_str})"
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=progress_text
        )
    except Exception as e:
        print(f"Error updating progress: {e}")


async def process_files(download_path, up_path, identifier):
    """Process downloaded files by adding watermarks"""
    for root, _, files in os.walk(download_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()
            
            # Check if it's an image or video
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.mkv']:
                # Add watermark using ffmpeg with force overwrite flag
                output_file = os.path.join(up_path, file)
                watermark_filter = f"drawtext=fontfile='{WATERMARK_FONT}':text='{WATERMARK_TEXT}':fontcolor={WATERMARK_COLOR}:fontsize={WATERMARK_FONTSIZE}:x={WATERMARK_POSITION_X}:y={WATERMARK_POSITION_Y}"
                
                if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                    # Add watermark to image
                    os.system(f'ffmpeg -y -i "{file_path}" -vf "{watermark_filter}" "{output_file}"')
                else:
                    # Add watermark to video
                    os.system(f'ffmpeg -y -i "{file_path}" -vf "{watermark_filter}" -codec:a copy "{output_file}"')
            else:
                # Copy other files directly
                shutil.copy(file_path, os.path.join(up_path, file))


async def upload_to_telegram(up_path, channel_name, message_text, identifier, context=None, chat_id=None):
    """Upload files to Telegram with progress reporting if context is provided"""
    global client
    
    # Get all files in the upload path
    files = []
    for root, _, filenames in os.walk(up_path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    
    if files:
        # Send progress message if context and chat_id are provided
        progress_message = None
        if context and chat_id:
            progress_message = await context.bot.send_message(
                chat_id=chat_id, 
                text="正在准备上传..."
            )
        
        start_time = time.time()
        
        # Upload files to the channel
        if len(files) == 1:
            # Single file upload with progress callback if available
            if progress_message:
                await client.send_file(
                    channel_name, 
                    files[0], 
                    caption=message_text,
                    progress_callback=lambda current, total: asyncio.create_task(
                        upload_progress_callback(
                            current, total, start_time, 
                            progress_message.message_id, chat_id, context
                        )
                    )
                )
            else:
                await client.send_file(channel_name, files[0], caption=message_text)
        else:
            # Group upload for multiple files
            if progress_message:
                await client.send_file(
                    channel_name, 
                    files, 
                    caption=message_text,
                    progress_callback=lambda current, total: asyncio.create_task(
                        upload_progress_callback(
                            current, total, start_time, 
                            progress_message.message_id, chat_id, context
                        )
                    )
                )
            else:
                await client.send_file(channel_name, files, caption=message_text)
        
        # Delete progress message after upload completes
        if progress_message:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=progress_message.message_id
            )


async def execute_fw_mark_task(task, context: ContextTypes.DEFAULT_TYPE):
    """Execute fw_mark task"""
    _, task_id, s_name, s_num, e_num, t_name = task
    output_dir = f"{HOME_PATH}/tdlbot"
    download_path = f"{HOME_PATH}/tdlbot/download/{task_id}"
    up_path = f"{HOME_PATH}/tdlbot/upload/{task_id}"
    
    # Get task_chat_map from the context
    task_chat_map = context.bot_data.get('task_chat_map', {})
    chat_id = task_chat_map.get(task_id)
    
    # Create necessary directories
    os.makedirs(download_path, exist_ok=True)
    os.makedirs(up_path, exist_ok=True)
    
    # Export raw message structure
    os.system(f'tdl -n lks chat export -c {s_name} -T id -i {s_num},{e_num} -o {output_dir}/output_raw_{task_id}.json --raw')
    
    # Notify user that export is complete and processing is beginning
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=f"任务ID: {task_id} 导出完成，开始处理...")
    
    # Read the raw output to process based on GroupedID
    with open(f"{output_dir}/output_raw_{task_id}.json", 'r') as f:
        raw_data = json.load(f)
    
    # Group messages by GroupedID
    grouped_messages = {}
    for msg in raw_data.get('messages', []):
        group_id = msg.get('raw', {}).get('GroupedID', 0)
        if group_id not in grouped_messages:
            grouped_messages[group_id] = []
        grouped_messages[group_id].append(msg)
    
    # Process each group - sort groups by minimum message ID to process from smallest to largest
    sorted_groups = sorted(grouped_messages.items(), key=lambda x: min(msg['id'] for msg in x[1]))
    
    for group_id, messages in sorted_groups:
        if group_id == 0:  # Non-grouped messages
            # Sort messages by ID in ascending order
            sorted_messages = sorted(messages, key=lambda x: x['id'])
            
            for msg in sorted_messages:
                msg_id = msg['id']
                # Export non-raw message for download
                os.system(f'tdl -n lks chat export -c {s_name} -T id -i {msg_id},{msg_id} -o {output_dir}/output_{task_id}_{msg_id}.json')
                
                # Download files
                os.system(f'tdl -n lks dl -f {output_dir}/output_{task_id}_{msg_id}.json -l 6 -t 16 --pool 8 --continue --reconnect-timeout 0 -d {download_path}')
                
                # Process downloaded files
                await process_files(download_path, up_path, msg_id)
                
                # Upload to target channel with message text and progress updates
                message_text = msg.get('raw', {}).get('Message', '')
                await upload_to_telegram(up_path, t_name, message_text, msg_id, context, chat_id)
                
                # Clean up downloaded and processed files immediately after upload
                os.remove(f"{output_dir}/output_{task_id}_{msg_id}.json")
                shutil.rmtree(download_path, ignore_errors=True)
                shutil.rmtree(up_path, ignore_errors=True)
                os.makedirs(download_path, exist_ok=True)
                os.makedirs(up_path, exist_ok=True)
        else:
            # Sort messages by ID in ascending order
            sorted_messages = sorted(messages, key=lambda x: x['id'])
            
            # Get min and max message IDs for this group
            min_id = sorted_messages[0]['id']
            max_id = sorted_messages[-1]['id']
            
            # Get the text from the message with minimum ID
            message_text = sorted_messages[0].get('raw', {}).get('Message', '')
            
            # Export non-raw message for download
            os.system(f'tdl -n lks chat export -c {s_name} -T id -i {min_id},{max_id} -o {output_dir}/output_{task_id}_{group_id}.json')
            
            # Download files
            os.system(f'tdl -n lks dl -f {output_dir}/output_{task_id}_{group_id}.json -l 6 -t 16 --pool 8 --continue --reconnect-timeout 0 -d {download_path}')
            
            # Process downloaded files
            await process_files(download_path, up_path, group_id)
            
            # Upload to target channel with message text from min_id message
            await upload_to_telegram(up_path, t_name, message_text, group_id, context, chat_id)
            
            # Clean up downloaded and processed files immediately after upload
            os.remove(f"{output_dir}/output_{task_id}_{group_id}.json")
            shutil.rmtree(download_path, ignore_errors=True)
            shutil.rmtree(up_path, ignore_errors=True)
            os.makedirs(download_path, exist_ok=True)
            os.makedirs(up_path, exist_ok=True)
    
    # Clean up remaining files
    os.remove(f"{output_dir}/output_raw_{task_id}.json")
    
    # Send completion notification
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=f"任务ID: {task_id} 的上传已完成。") 
