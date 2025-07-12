import logging
import uuid
import schedule
import time
import os
import json
from datetime import datetime, timedelta
import pytz
import telebot
from telebot import types
import requests
import re
import schedule
import threading
import traceback
import math
import requests
import subprocess

# تنظیم لاگ‌گذاری برای دیباگ و ردیابی خطاها
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تنظیمات اولیه بات با توکن
TOKEN = '8042250767:AAFdQHSifLCR_7KXvPfA5M8noErZ969N_A0'
ADMIN_ID = 1113652228
OWNER_ID = 1113652228
BOT_VERSION = "4.3"

# ایجاد نمونه بات
bot = telebot.TeleBot(TOKEN)

# کلاس ذخیره‌سازی داده‌ها برای مدیریت تمام اطلاعات
class DataStore:
    def __init__(self, base_folder="central_data", token=None):
        self.base_folder = base_folder
        self.mandatory_channels = []  # لیست چنل‌های جوین اجباری
        self.mandatory_join_message = "برای استفاده از ربات باید عضو چنل‌های زیر شوید."
        self.mandatory_seen_channels = []
        self.mandatory_seen_message = "برای ادامه باید پست‌های چنل‌های زیر را سین بزنید."
        self.mandatory_seen_count = 0
        self.mandatory_reaction_channels = []
        self.mandatory_reaction_message = "برای ادامه باید به پست‌های چنل‌های زیر ری‌اکشن بزنید."

        os.makedirs(self.base_folder, exist_ok=True)
        self.user_data_path = os.path.join(self.base_folder, "user_data.json")
        self.user_data = {}
        if token is not None:
            with open(os.path.join(self.base_folder, "bot_token.txt"), "w", encoding="utf-8") as f:
                f.write(token)
        self.signatures = {
            "Default": {
                "template": "{Bold}\n\n{BlockQuote}\n\n{Simple}\n\n{Italic}\n\n{Code}\n\n{Strike}\n\n{Underline}\n\n{Spoiler}\n\n{Link}",
                "variables": ["Bold", "BlockQuote", "Simple", "Italic", "Code", "Strike", "Underline", "Spoiler", "Link"]
            }
        }
        self.broadcast_users = []
        self.variables = {}
        self.default_values = {}
        self.user_states = {}
        self.settings = {
            "default_welcome": "🌟 خوش آمدید {name} عزیز! 🌟\n\nبه ربات مدیریت پست و امضا خوش آمدید."
        }
        self.channels = []
        self.uploader_channels = []
        self.scheduled_posts = []
        self.scheduled_broadcasts = []
        self.file_details = []
        self.admins = [OWNER_ID]
        self.admin_permissions = {str(OWNER_ID): {
            "create_post": True,
            "signature_management": True,
            "variable_management": True,
            "default_values_management": True,
            "default_settings": True,
            "register_channel": True,
            "manage_timers": True,
            "options_management": True,
            "admin_management": True,
            "uploader_management": True,
            "broadcast_management": True,
            "bot_creator": True,
            "user_account": True
        }}
        self.timer_settings = {
            "timers_enabled": True,
            "inline_buttons_enabled": True
        }
        self.last_message_id = {}
        self.last_user_message_id = {}
        self.state_messages = {
            None: "در حال حاضر در منوی اصلی هستید.",
            "signature_management": "در حال حاضر در حال مدیریت امضاها هستید.",
            "select_signature": "در حال حاضر در حال انتخاب امضا هستید.",
            "post_with_signature_media": "در حال حاضر در حال ارسال رسانه برای پست هستید.",
            "post_with_signature_values": "در حال حاضر در حال وارد کردن مقادیر پست هستید.",
            "post_with_signature_ready": "",
            "new_signature_name": "در حال حاضر در حال وارد کردن نام امضای جدید هستید.",
            "new_signature_template": "در حال حاضر در حال وارد کردن قالب امضا هستید.",
            "delete_signature": "در حال حاضر در حال حذف امضا هستید.",
            "admin_management": "در حال حاضر در حال مدیریت ادمین‌ها هستید.",
            "add_admin": "در حال حاضر در حال افزودن ادمین هستید.",
            "remove_admin": "در حال حاضر در حال حذف ادمین هستید.",
            "list_admins": "در حال حاضر در حال مشاهده لیست ادمین‌ها هستید.",
            "variable_management": "در حال حاضر در حال مدیریت متغیرها هستید.",
            "select_variable_format": "در حال حاضر در حال انتخاب نوع متغیر هستید.",
            "add_variable": "در حال حاضر در حال افزودن متغیر جدید هستید.",
            "remove_variable": "در حال حاضر در حال حذف متغیر هستید.",
            "set_default_settings": "در حال حاضر در حال تنظیم متن پیش‌فرض هستید.",
            "register_channel": "در حال حاضر در حال ثبت چنل هستید.",
            "set_timer": "در حال حاضر در حال تنظیم تایمر هستید.",
            "ask_for_inline_buttons": "در حال حاضر در حال پرسیدن برای افزودن کلید شیشه‌ای هستید.",
            "add_inline_button_name": "در حال حاضر در حال وارد کردن نام کلید شیشه‌ای هستید.",
            "add_inline_button_url": "در حال حاضر در حال وارد کردن لینک کلید شیشه‌ای هستید.",
            "ask_continue_adding_buttons": "در حال حاضر در حال پرسیدن برای ادامه افزودن کلیدها هستید.",
            "select_button_position": "در حال حاضر در حال انتخاب نحوه نمایش کلید شیشه‌ای بعدی هستید.",
            "schedule_post": "در حال حاضر در حال زمان‌بندی پست هستید.",
            "select_channel_for_post": "در حال حاضر در حال انتخاب چنل برای ارسال پست هستید.",
            "timer_inline_management": "در حال حاضر در حال مدیریت تایمرها و کلیدهای شیشه‌ای هستید.",
            "default_values_management": "در حال حاضر در حال مدیریت مقادیر پیش‌فرض هستید.",
            "set_default_value_select_var": "در حال حاضر در حال انتخاب متغیر برای تنظیم مقدار پیش‌فرض هستید.",
            "set_default_value": "در حال حاضر در حال وارد کردن مقدار پیش‌فرض هستید.",
            "remove_default_value": "در حال حاضر در حال حذف مقدار پیش‌فرض هستید.",
            "select_admin_for_permissions": "در حال حاضر در حال انتخاب ادمین برای تنظیم دسترسی‌ها هستید.",
            "manage_admin_permissions": "در حال حاضر در حال تنظیم دسترسی‌های ادمین هستید.",
            "uploader_menu": "در حال حاضر در منوی اپلودر هستید.",
            "uploader_file_upload": "در حال حاضر در حال اپلود فایل هستید.",
        }
        self.uploader_file_map = {}
        self.uploader_file_map_path = os.path.join(self.base_folder, 'uploader_files.json')
        self.stats_path = os.path.join(self.base_folder, 'stats.json')
        self.create_default_files()
        self.load_data()
        
    def create_default_files(self):
        default_files = {
            'mandatory_channels.json': [],
            'mandatory_join_message.txt': "برای استفاده از ربات باید عضو چنل‌های زیر شوید.",
            'mandatory_seen_channels.json': [],
            'mandatory_seen_message.txt': "برای ادامه باید پست‌های چنل‌های زیر را سین بزنید.",
            'mandatory_seen_count.json': 0,
            'mandatory_reaction_channels.json': [],
            'mandatory_reaction_message.txt': "برای ادامه باید به پست‌های چنل‌های زیر ری‌اکشن بزنید.",
            'signatures.json': self.signatures,
            'scheduled_broadcasts.json': [],
            'variables.json': {
                "Bold": {"format": "Bold"},
                "BlockQuote": {"format": "BlockQuote"},
                "Simple": {"format": "Simple"},
                "Italic": {"format": "Italic"},
                "Code": {"format": "Code"},
                "Strike": {"format": "Strike"},
                "Underline": {"format": "Underline"},
                "Spoiler": {"format": "Spoiler"},
                "Link": {"format": "Link"}
            },
            'default_values.json': {},
            'user_data.json': {},
            'settings.json': self.settings,
            'channels.json': [],
            'uploader_channels.json': [],
            'admins.json': [OWNER_ID],
            'admin_permissions.json': self.admin_permissions,
            'timer_settings.json': self.timer_settings,
            'uploader_files.json': {},
            'stats.json': {
                "uploader_files_total": 0,
                "uploader_files_total_size_mb": 0.0,
                "last_updated": "",
            }
        }
        for file_name, default_content in default_files.items():
            file_path = os.path.join(self.base_folder, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f, ensure_ascii=False, indent=4)
                    
    def load_data(self):
        def _load(file, attr, default):
            path = os.path.join(self.base_folder, file)
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        setattr(self, attr, json.load(f))
            except Exception:
                setattr(self, attr, default)

        _load('signatures.json', 'signatures', {})
        _load('variables.json', 'controls', {})
        _load('default_values.json', 'default_values', {})
        _load('user_data.json', 'user_data', {})
        _load('scheduled_broadcasts.json', 'scheduled_broadcasts', [])
        _load('settings.json', 'settings', {})
        _load('channels.json', 'channels', [])
        _load('uploader_channels.json', 'uploader_channels', [])
        _load('uploader_files.json', 'uploader_file_map', {})
        _load('admins.json', 'admins', [])
        _load('admin_permissions.json', 'admin_permissions', {})
        _load('timer_settings.json', 'timer_settings', {})
        _load('mandatory_channels.json', 'mandatory_channels', [])
        _load('mandatory_seen_channels.json', 'mandatory_seen_channels', [])
        _load('mandatory_seen_count.json', 'mandatory_seen_count', 0)
        _load('mandatory_reaction_channels.json', 'mandatory_reaction_channels', [])
        # پیام‌ها:
        try:
            with open(os.path.join(self.base_folder, 'mandatory_join_message.txt'), 'r', encoding='utf-8') as f:
                self.mandatory_join_message = f.read()
            with open(os.path.join(self.base_folder, 'mandatory_seen_message.txt'), 'r', encoding='utf-8') as f:
                self.mandatory_seen_message = f.read()
            with open(os.path.join(self.base_folder, 'mandatory_reaction_message.txt'), 'r', encoding='utf-8') as f:
                self.mandatory_reaction_message = f.read()
        except:
            pass
        if os.path.exists(self.stats_path):
            with open(self.stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                self.uploader_files_total = stats.get('uploader_files_total', 0)
                self.uploader_files_total_size_mb = stats.get('uploader_files_total_size_mb', 0.0)
        else:
            self.uploader_files_total = 0
            self.uploader_files_total_size_mb = 0.0

    def save_data(self):
        def _save(file, value):
            path = os.path.join(self.base_folder, file)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=4)
        _save('signatures.json', self.signatures)
        _save('variables.json', getattr(self, 'controls', {}))
        _save('default_values.json', self.default_values)
        _save('user_data.json', self.user_data)
        _save('scheduled_broadcasts.json', self.scheduled_broadcasts)
        _save('settings.json', self.settings)
        _save('channels.json', self.channels)
        _save('uploader_channels.json', self.uploader_channels)
        _save('uploader_files.json', self.uploader_file_map)
        _save('admins.json', self.admins)
        _save('admin_permissions.json', self.admin_permissions)
        _save('timer_settings.json', self.timer_settings)
        _save('mandatory_channels.json', self.mandatory_channels)
        _save('mandatory_seen_channels.json', self.mandatory_seen_channels)
        _save('mandatory_seen_count.json', self.mandatory_seen_count)
        _save('mandatory_reaction_channels.json', self.mandatory_reaction_channels)
        with open(os.path.join(self.base_folder, 'mandatory_join_message.txt'), 'w', encoding='utf-8') as f:
            f.write(self.mandatory_join_message)
        with open(os.path.join(self.base_folder, 'mandatory_seen_message.txt'), 'w', encoding='utf-8') as f:
            f.write(self.mandatory_seen_message)
        with open(os.path.join(self.base_folder, 'mandatory_reaction_message.txt'), 'w', encoding='utf-8') as f:
            f.write(self.mandatory_reaction_message)
           
        stats = {
            "uploader_files_total": getattr(self, 'uploader_files_total', 0),
            "uploader_files_total_size_mb": getattr(self, 'uploader_files_total_size_mb', 0.0),
            "last_updated": "",
        }
        _save('stats.json', stats)

    def get_user_state(self, user_id):
        if str(user_id) not in self.user_states:
            self.user_states[str(user_id)] = {
                "state": None,
                "data": {}
            }
        return self.user_states[str(user_id)]

    def update_user_state(self, user_id, state=None, data=None):
        if str(user_id) not in self.user_states:
            self.user_states[str(user_id)] = {
                "state": None,
                "data": {}
            }
        if state is not None:
            self.user_states[str(user_id)]["state"] = state
        if data is not None:
            self.user_states[str(user_id)]["data"].update(data)

    def reset_user_state(self, user_id):
        self.user_states[str(user_id)] = {
            "state": None,
            "data": {}
        }
 
data_store = DataStore(base_folder="central_data", token=TOKEN)

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return user_id in data_store.admins

def get_bot_token_from_folder(base_folder):
    token_file = os.path.join(base_folder, "bot_token.txt")
    with open(token_file, "r", encoding="utf-8") as f:
        return f.read().strip()

# منوی فرعی برای مدیریت تایمرها و کلیدهای شیشه‌ای
def get_timer_inline_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    timers_enabled = data_store.timer_settings.get("timers_enabled", True)
    inline_buttons_enabled = data_store.timer_settings.get("inline_buttons_enabled", True)
    
    timers_btn_text = "✅ تایمرها: فعال" if timers_enabled else "❌ تایمرها: غیرفعال"
    inline_buttons_btn_text = "✅ کلیدهای شیشه‌ای: فعال" if inline_buttons_enabled else "❌ کلیدهای شیشه‌ای: غیرفعال"
    
    timers_btn = types.KeyboardButton(timers_btn_text)
    inline_buttons_btn = types.KeyboardButton(inline_buttons_btn_text)
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    
    markup.add(timers_btn)
    markup.add(inline_buttons_btn)
    markup.add(back_btn)
    return markup

def get_uploader_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    upload_file_btn = types.KeyboardButton("⬆️ اپلود فایل")
    register_uploader_channel_btn = types.KeyboardButton("📢 ثبت چنل اپلودری")
    edit_file_btn = types.KeyboardButton("🛠️ ویرایش فایل")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(upload_file_btn)
    markup.add(register_uploader_channel_btn)
    markup.add(edit_file_btn)
    markup.add(back_btn)
    return markup

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] in ["uploader_menu", None] and message.text == "📢 ثبت چنل اپلودری")
def uploader_register_channel_entry(message):
    user_id = message.from_user.id
    data_store.update_user_state(user_id, "register_uploader_channel")
    status_text = data_store.state_messages.get("register_uploader_channel", "")
    bot.send_message(user_id, f"{status_text}\n\n🖊️ آیدی چنل اپلودری را وارد کنید (مثال: @channelname):", reply_markup=get_back_menu())

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "register_uploader_channel" and message.text == "🔙 بازگشت به منوی اصلی")
def back_from_register_uploader_channel(message):
    user_id = message.from_user.id
    data_store.reset_user_state(user_id)
    bot.send_message(user_id, "🏠 بازگشت به منوی اصلی:", reply_markup=get_main_menu(user_id))

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "register_uploader_channel")
def handle_register_uploader_channel(message):
    user_id = message.from_user.id
    channel_name = message.text.strip()
    status_text = data_store.state_messages.get("register_uploader_channel", "")
    if not channel_name.startswith('@'):
        bot.send_message(user_id, f"{status_text}\n\n⚠️ آیدی چنل باید با @ شروع شود (مثال: @channelname).", reply_markup=get_back_menu())
        return
    try:
        chat = bot.get_chat(channel_name)
        bot_member = bot.get_chat_member(channel_name, bot.get_me().id)
        logger.info(f"Bot member info: {vars(bot_member)}")
        if bot_member.status not in ['administrator', 'creator']:
            bot.send_message(user_id, f"{status_text}\n\n⚠️ ربات باید ادمین باشد.", reply_markup=get_back_menu())
            return
        can_post = getattr(bot_member, "can_post_messages", None)
        can_edit = getattr(bot_member, "can_edit_messages", None)
        can_delete = getattr(bot_member, "can_delete_messages", None)
        can_promote = getattr(bot_member, "can_promote_members", None)
        required_permissions = [
            ("ارسال پیام", can_post),
            ("ویرایش پیام‌های دیگران", can_edit),
            ("حذف پیام‌های دیگران", can_delete),
            ("ادمین کردن کاربران", can_promote)
        ]
        if not all(granted or granted is None for _, granted in required_permissions):
            permissions_text = "\n".join(
                f"{name}: {'✅' if granted or granted is None else '❌'}" for name, granted in required_permissions
            )
            bot.send_message(
                user_id,
                f"{status_text}\n\n⚠️ هیچ قابلیتی بهم ندادی!\n{permissions_text}\nلطفاً دسترسی‌های لازم را بدهید.",
                reply_markup=get_back_menu()
            )
            return
        if channel_name in data_store.uploader_channels:
            bot.send_message(user_id, f"{status_text}\n\n⚠️ این چنل اپلودری قبلاً ثبت شده است.", reply_markup=get_back_menu())
            return
        data_store.uploader_channels.append(channel_name)
        data_store.save_data()
        permissions_text = "\n".join(
            f"{name}: {'✅' if granted or granted is None else '❌'}" for name, granted in required_permissions
        )
        bot.send_message(
            user_id,
            f"{status_text}\n\n{permissions_text}\n✅ چنل اپلودری {channel_name} چک شد و ذخیره شد.\n🏠 منوی اصلی:",
            reply_markup=get_main_menu(user_id)
        )
        data_store.reset_user_state(user_id)
    except Exception as e:
        logger.error(f"خطا در بررسی دسترسی چنل اپلودری: {e}")
        bot.send_message(
            user_id,
            f"{status_text}\n\n⚠️ خطا در بررسی چنل {channel_name}. مطمئن شوید که ربات ادمین است و دوباره امتحان کنید.",
            reply_markup=get_back_menu()
        )

def get_uploader_finish_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    finish_btn = types.KeyboardButton("✅ پایان اپلود")
    back_btn = types.KeyboardButton("🔙 بازگشت به اپلودر")
    markup.add(finish_btn)
    markup.add(back_btn)
    return markup

# منوی مدیریت ادمین‌ها
def get_admin_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    add_admin_btn = types.KeyboardButton("➕ افزودن ادمین")
    remove_admin_btn = types.KeyboardButton("➖ حذف ادمین")
    list_admins_btn = types.KeyboardButton("👀 لیست ادمین‌ها")
    permissions_btn = types.KeyboardButton("🔧 تنظیم دسترسی ادمین‌ها")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(add_admin_btn, remove_admin_btn)
    markup.add(list_admins_btn, permissions_btn)
    markup.add(back_btn)
    return markup

def get_admin_permissions_menu(admin_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    permissions = data_store.admin_permissions.get(str(admin_id), {
        "create_post": False,
        "signature_management": False,
        "variable_management": False,
        "default_values_management": False,
        "default_settings": False,
        "register_channel": False,
        "manage_timers": False,
        "options_management": False,
        "admin_management": False,
        "uploader_management": False,
        "broadcast_management": False,
        "bot_creator": False,
        "user_account": False,
        "ai": False
    })
    
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('create_post', False) else '❌'} ایجاد پست"),
        types.KeyboardButton(f"{'✅' if permissions.get('signature_management', False) else '❌'} مدیریت امضاها")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('variable_management', False) else '❌'} مدیریت متغیرها"),
        types.KeyboardButton(f"{'✅' if permissions.get('default_values_management', False) else '❌'} مقادیر پیش‌فرض")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('default_settings', False) else '❌'} تنظیمات پیش‌فرض"),
        types.KeyboardButton(f"{'✅' if permissions.get('register_channel', False) else '❌'} ثبت چنل")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('manage_timers', False) else '❌'} مدیریت تایمرها"),
        types.KeyboardButton(f"{'✅' if permissions.get('options_management', False) else '❌'} مدیریت اپشن‌ها")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('admin_management', False) else '❌'} مدیریت ادمین‌ها"),
        types.KeyboardButton(f"{'✅' if permissions.get('uploader_management', False) else '❌'} اپلودر")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('broadcast_management', False) else '❌'} ارسال همگانی"),
        types.KeyboardButton(f"{'✅' if permissions.get('bot_creator', False) else '❌'} ربات ساز")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('user_account', False) else '❌'} حساب کاربری"),
        types.KeyboardButton(f"{'✅' if permissions.get('ai', False) else '❌'} هوش مصنوعی")
    )
    markup.add(types.KeyboardButton("🔙 بازگشت به مدیریت ادمین"))
    return markup

# منوی اصلی برای دسترسی به امکانات بات
def get_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if is_owner(user_id):
        markup.add(types.KeyboardButton("🆕 ایجاد پست"))
        markup.add(types.KeyboardButton("✍️ مدیریت امضاها"), types.KeyboardButton("⚙️ مدیریت متغیرها"))
        markup.add(types.KeyboardButton("📝 مدیریت مقادیر پیش‌فرض"))
        markup.add(types.KeyboardButton("🏠 تنظیمات پیش‌فرض"), types.KeyboardButton("✨ مدیریت اپشن‌ها"))
        markup.add(types.KeyboardButton("📢 ثبت چنل"), types.KeyboardButton("⏰ مدیریت تایمرها"))
        markup.add(types.KeyboardButton("📤 اپلودر"), types.KeyboardButton("📣 ارسال همگانی"))
        markup.add(types.KeyboardButton("🤖 هوش مصنوعی"), types.KeyboardButton("🤖 ربات ساز"))
        markup.add(types.KeyboardButton("👤 حساب کاربری"), types.KeyboardButton("👤 مدیریت ادمین‌ها"))
        markup.add(types.KeyboardButton("🛡️ امکانات اجباری"))
        markup.add(types.KeyboardButton(f"🤖 بات دستیار نسخه {BOT_VERSION}"))
    elif user_id in data_store.admins:
        permissions = data_store.admin_permissions.get(str(user_id), {})
        if permissions.get("create_post"):
            markup.add(types.KeyboardButton("🆕 ایجاد پست"))
        if permissions.get("signature_management"):
            markup.add(types.KeyboardButton("✍️ مدیریت امضاها"))
        if permissions.get("variable_management"):
            markup.add(types.KeyboardButton("⚙️ مدیریت متغیرها"))
        if permissions.get("default_values_management"):
            markup.add(types.KeyboardButton("📝 مدیریت مقادیر پیش‌فرض"))
        if permissions.get("default_settings"):
            markup.add(types.KeyboardButton("🏠 تنظیمات پیش‌فرض"))
        if permissions.get("register_channel"):
            markup.add(types.KeyboardButton("📢 ثبت چنل"))
        if permissions.get("manage_timers"):
            markup.add(types.KeyboardButton("⏰ مدیریت تایمرها"))
        if permissions.get("options_management"):
            markup.add(types.KeyboardButton("✨ مدیریت اپشن‌ها"))
        if permissions.get("uploader_management"):
            markup.add(types.KeyboardButton("📤 اپلودر"))
        if permissions.get("broadcast_management"):
            markup.add(types.KeyboardButton("📣 ارسال همگانی"))
        if permissions.get("ai"):
            markup.add(types.KeyboardButton("🤖 هوش مصنوعی"))
        if permissions.get("mandatory_features"):
            markup.add(types.KeyboardButton("🛡️ امکانات اجباری"))
        if permissions.get("bot_creator"):
            markup.add(types.KeyboardButton("🤖 ربات ساز"))
        markup.add(types.KeyboardButton("👤 حساب کاربری"))
        markup.add(types.KeyboardButton(f"🤖 بات دستیار نسخه {BOT_VERSION}"))
    else:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton("👤 حساب کاربری"))
        markup.add(types.KeyboardButton(f"🤖 بات دستیار نسخه {BOT_VERSION}"))
    return markup

# منوی بازگشت برای راحتی کاربر
def get_back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(back_btn)
    return markup

# منوی انتخاب نحوه نمایش کلیدهای شیشه‌ای
def get_button_layout_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    inline_btn = types.KeyboardButton("📏 به کنار")
    stacked_btn = types.KeyboardButton("📐 به پایین")
    markup.add(inline_btn, stacked_btn)
    markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    return markup

# مدیریت ادمین‌ها
def handle_admin_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    logger.info(f"پردازش پیام در handle_admin_management، متن: '{text}'، حالت: {state}")
    
    if text == "➕ افزودن ادمین":
        logger.info(f"تغییر حالت به add_admin برای کاربر {user_id}")
        data_store.update_user_state(user_id, "add_admin")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id, 0),
                text=f"{status_text}\n\n🖊️ آیدی عددی کاربر را برای افزودن به ادمین‌ها وارد کنید:",
                reply_markup=get_back_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای افزودن ادمین: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ آیدی عددی کاربر را برای افزودن به ادمین‌ها وارد کنید:", reply_markup=get_back_menu())
            data_store.last_message_id[user_id] = msg.message_id
            
    elif text == "➖ حذف ادمین":
        logger.info(f"تغییر حالت به remove_admin برای کاربر {user_id}")
        if len(data_store.admins) <= 1:  # جلوگیری از حذف تنها ادمین (اونر)
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ حداقل یک ادمین (اونر) باید باقی بماند.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ حداقل یک ادمین (اونر) باید باقی بماند.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for admin_id in data_store.admins:
            if admin_id != OWNER_ID:  # اونر قابل حذف نیست
                markup.add(types.KeyboardButton(str(admin_id)))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "remove_admin")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id, 0),
                text=f"{status_text}\n\n🗑️ آیدی ادمینی که می‌خواهید حذف کنید را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ آیدی ادمینی که می‌خواهید حذف کنید را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "👀 لیست ادمین‌ها":
        logger.info(f"نمایش لیست ادمین‌ها برای کاربر {user_id}")
        admins_text = f"{status_text}\n\n👤 لیست ادمین‌ها:\n\n"
        if not data_store.admins:
            admins_text += "هیچ ادمینی وجود ندارد.\n"
        else:
            for admin_id in data_store.admins:
                admins_text += f"🔹 آیدی: {admin_id}\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id, 0),
                text=admins_text,
                reply_markup=get_admin_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, admins_text, reply_markup=get_admin_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "admin_management")

    elif text == "🔧 تنظیم دسترسی ادمین‌ها":
            if not data_store.admins:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ هیچ ادمینی وجود ندارد.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ ادمینی وجود ندارد.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                return
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for admin_id in data_store.admins:
                markup.add(types.KeyboardButton(str(admin_id)))
            markup.add(types.KeyboardButton("🔙 بازگشت به مدیریت ادمین"))
            data_store.update_user_state(user_id, "select_admin_for_permissions")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n🔧 آیدی ادمینی که می‌خواهید دسترسی‌هایش را تنظیم کنید را انتخاب کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🔧 آیدی ادمینی که می‌خواهید دسترسی‌هایش را تنظیم کنید را انتخاب کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        
    elif state == "select_admin_for_permissions":
        try:
            admin_id = int(text.strip())
            if admin_id == OWNER_ID:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ دسترسی‌های اونر قابل تغییر نیست.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ دسترسی‌های اونر قابل تغییر نیست.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                data_store.update_user_state(user_id, "admin_management")
                return
            if admin_id in data_store.admins:
                data_store.update_user_state(user_id, "manage_admin_permissions", {"selected_admin_id": admin_id})
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n🔧 تنظیم دسترسی‌های ادمین {admin_id}:",
                        reply_markup=get_admin_permissions_menu(admin_id)
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n🔧 تنظیم دسترسی‌های ادمین {admin_id}:", reply_markup=get_admin_permissions_menu(admin_id))
                    data_store.last_message_id[user_id] = msg.message_id
            else:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ این آیدی در لیست ادمین‌ها نیست.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این آیدی در لیست ادمین‌ها نیست.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                data_store.update_user_state(user_id, "admin_management")
        except ValueError:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
    
    elif state == "manage_admin_permissions":
        admin_id = user_state["data"]["selected_admin_id"]
        permissions = data_store.admin_permissions.get(str(admin_id), {
            "create_post": False,
            "signature_management": False,
            "variable_management": False,
            "default_values_management": False,
            "default_settings": False,
            "register_channel": False,
            "manage_timers": False,
            "options_management": False,
            "admin_management": False
        })
        permission_map = {
            "✅ ایجاد پست": ("create_post", True),
            "❌ ایجاد پست": ("create_post", False),
            "✅ مدیریت امضاها": ("signature_management", True),
            "❌ مدیریت امضاها": ("signature_management", False),
            "✅ مدیریت متغیرها": ("variable_management", True),
            "❌ مدیریت متغیرها": ("variable_management", False),
            "✅ مقادیر پیش‌فرض": ("default_values_management", True),
            "❌ مقادیر پیش‌فرض": ("default_values_management", False),
            "✅ تنظیمات پیش‌فرض": ("default_settings", True),
            "❌ تنظیمات پیش‌فرض": ("default_settings", False),
            "✅ ثبت چنل": ("register_channel", True),
            "❌ ثبت چنل": ("register_channel", False),
            "✅ مدیریت تایمرها": ("manage_timers", True),
            "❌ مدیریت تایمرها": ("manage_timers", False),
            "✅ مدیریت اپشن‌ها": ("options_management", True),
            "❌ مدیریت اپشن‌ها": ("options_management", False),
            "✅ مدیریت ادمین‌ها": ("admin_management", True),
            "❌ مدیریت ادمین‌ها": ("admin_management", False),
            "✅ اپلودر": ("uploader_management", True),  # اضافه شد
            "❌ اپلودر": ("uploader_management", False), 
            "✅ ارسال همگانی": ("broadcast_management", True),
            "❌ ارسال همگانی": ("broadcast_management", False),
            "✅ ربات ساز": ("bot_creator", True),
            "❌ ربات ساز": ("bot_creator", False),
            "✅ حساب کاربری": ("user_account", True),
            "❌ حساب کاربری": ("user_account", False),
        }

        if text == "🔙 بازگشت به مدیریت ادمین":
            data_store.update_user_state(user_id, "admin_management")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n👤 مدیریت ادمین‌ها:",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n👤 مدیریت ادمین‌ها:", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        elif text in permission_map:
            perm_key, new_value = permission_map[text]
            permissions[perm_key] = not permissions.get(perm_key, False)
            data_store.admin_permissions[str(admin_id)] = permissions
            data_store.save_data()
            action_text = "فعال شد" if not permissions[perm_key] else "غیرفعال شد"
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n✅ دسترسی '{perm_key}' {action_text}.\n🔧 تنظیم دسترسی‌های ادمین {admin_id}:",
                    reply_markup=get_admin_permissions_menu(admin_id)
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ دسترسی '{perm_key}' {action_text}.\n🔧 تنظیم دسترسی‌های ادمین {admin_id}:", reply_markup=get_admin_permissions_menu(admin_id))
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ گزینه نامعتبر. لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
                    reply_markup=get_admin_permissions_menu(admin_id)
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ گزینه نامعتبر. لطفاً یکی از گزینه‌های منو را انتخاب کنید.", reply_markup=get_admin_permissions_menu(admin_id))
                data_store.last_message_id[user_id] = msg.message_id

    elif state == "add_admin":
        logger.info(f"تلاش برای افزودن ادمین با آیدی: '{text}'")
        try:
            admin_id = int(text.strip())
            logger.info(f"آیدی تبدیل‌شده: {admin_id}")
            if admin_id in data_store.admins:
                logger.warning(f"آیدی {admin_id} قبلاً در لیست ادمین‌ها وجود دارد.")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ این کاربر قبلاً ادمین است.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این کاربر قبلاً ادمین است.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                data_store.update_user_state(user_id, "admin_management")
                return
            logger.info(f"لیست ادمین‌ها قبل از افزودن: {data_store.admins}")
            data_store.admins.append(admin_id)
            # مقداردهی اولیه دسترسی‌های ادمین جدید
            data_store.admin_permissions[str(admin_id)] = {
                "create_post": False,
                "signature_management": False,
                "variable_management": False,
                "default_values_management": False,
                "default_settings": False,
                "register_channel": False,
                "manage_timers": False,
                "options_management": False,
                "admin_management": False,
                "uploader_management": False,
                "broadcast_management": False,
                "bot_creator": False,
                "user_account": False,
                "ai": False
            }
            logger.info(f"لیست ادمین‌ها بعد از افزودن: {data_store.admins}")
            if data_store.save_data():
                logger.info(f"آیدی {admin_id} با موفقیت به ادمین‌ها اضافه و ذخیره شد.")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n✅ کاربر با آیدی {admin_id} به ادمین‌ها اضافه شد.\n👤 مدیریت ادمین‌ها:",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n✅ کاربر با آیدی {admin_id} به ادمین‌ها اضافه شد.\n👤 مدیریت ادمین‌ها:", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            else:
                logger.error(f"خطا در ذخیره‌سازی آیدی {admin_id} در فایل admins.json")
                data_store.admins.remove(admin_id)
                del data_store.admin_permissions[str(admin_id)]
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ خطا در ذخیره‌سازی ادمین. لطفاً دوباره امتحان کنید.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ذخیره‌سازی ادمین. لطفاً دوباره امتحان کنید.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "admin_management")
        except ValueError as ve:
            logger.error(f"آیدی نامعتبر وارد شده: '{text}', خطا: {ve}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
    
    elif state == "remove_admin":
        logger.info(f"تلاش برای حذف ادمین با آیدی: '{text}'")
        try:
            admin_id = int(text.strip())
            logger.info(f"آیدی تبدیل‌شده: {admin_id}")
            if admin_id == OWNER_ID:
                logger.warning(f"تلاش برای حذف اونر با آیدی {admin_id}")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ اونر قابل حذف نیست.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ اونر قابل حذف نیست.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                data_store.update_user_state(user_id, "admin_management")
                return
            if admin_id in data_store.admins:
                logger.info(f"لیست ادمین‌ها قبل از حذف: {data_store.admins}")
                data_store.admins.remove(admin_id)
                logger.info(f"لیست ادمین‌ها بعد از حذف: {data_store.admins}")
                if data_store.save_data():
                    logger.info(f"آیدی {admin_id} با موفقیت از ادمین‌ها حذف شد.")
                    try:
                        bot.edit_message_text(
                            chat_id=user_id,
                            message_id=data_store.last_message_id.get(user_id, 0),
                            text=f"{status_text}\n\n✅ ادمین با آیدی {admin_id} حذف شد.\n👤 مدیریت ادمین‌ها:",
                            reply_markup=get_admin_management_menu()
                        )
                    except Exception as e:
                        logger.error(f"خطا در ویرایش پیام: {e}")
                        msg = bot.send_message(user_id, f"{status_text}\n\n✅ ادمین با آیدی {admin_id} حذف شد.\n👤 مدیریت ادمین‌ها:", reply_markup=get_admin_management_menu())
                        data_store.last_message_id[user_id] = msg.message_id
                else:
                    logger.error(f"خطا در ذخیره‌سازی پس از حذف آیدی {admin_id}")
                    data_store.admins.append(admin_id)  # rollback در صورت خطا
                    try:
                        bot.edit_message_text(
                            chat_id=user_id,
                            message_id=data_store.last_message_id.get(user_id, 0),
                            text=f"{status_text}\n\n⚠️ خطا در ذخیره‌سازی پس از حذف ادمین. لطفاً دوباره امتحان کنید.",
                            reply_markup=get_admin_management_menu()
                        )
                    except Exception as e:
                        logger.error(f"خطا در ویرایش پیام: {e}")
                        msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ذخیره‌سازی پس از حذف ادمین. لطفاً دوباره امتحان کنید.", reply_markup=get_admin_management_menu())
                        data_store.last_message_id[user_id] = msg.message_id
            else:
                logger.warning(f"آیدی {admin_id} در لیست ادمین‌ها نیست.")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ این آیدی در لیست ادمین‌ها نیست.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این آیدی در لیست ادمین‌ها نیست.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "admin_management")
        except ValueError as ve:
            logger.error(f"آیدی نامعتبر برای حذف: '{text}', خطا: {ve}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در حذف ادمین: {e}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ خطای غیرمنتظره رخ داد. لطفاً دوباره امتحان کنید.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as ex:
                logger.error(f"خطا در ویرایش پیام: {ex}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطای غیرمنتظره رخ داد. لطفاً دوباره امتحان کنید.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
                
# منوی مدیریت امضاها
def get_signature_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    view_btn = types.KeyboardButton("👀 مشاهده امضاها")
    add_btn = types.KeyboardButton("➕ افزودن امضای جدید")
    delete_btn = types.KeyboardButton("🗑️ حذف امضا")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(view_btn, add_btn)
    markup.add(delete_btn, back_btn)
    return markup

# دکمه‌های منو برای دسترسی سریع
MAIN_MENU_BUTTONS = [
    "🆕 ایجاد پست",
    "✍️ مدیریت امضاها",
    "⚙️ مدیریت متغیرها",
    "📝 مدیریت مقادیر پیش‌فرض",
    "🏠 تنظیمات پیش‌فرض",
    "📢 ثبت چنل",
    "⏰ مدیریت تایمرها",
    "✨ مدیریت اپشن‌ها",
    "👤 مدیریت ادمین‌ها",
    f"🤖 بات دستیار نسخه {BOT_VERSION}",
    "🔙 بازگشت به منوی اصلی",
    "⏭️ رد کردن مرحله رسانه",
    "🆕 پست جدید",
    "⏭️ پایان ارسال رسانه",
    "📏 به کنار",
    "📐 به پایین",
    "⏰ زمان‌بندی پست",
    "✅ ادامه دادن",
    "✅ بله",
    "❌ خیر",
    "Bold",
    "Italic",
    "Code",
    "Strike",
    "Underline",
    "Spoiler",
    "BlockQuote",
    "Simple",
    "✅ تایمرها: فعال", "❌ تایمرها: غیرفعال",
    "✅ کلیدهای شیشه‌ای: فعال",
    "❌ کلیدهای شیشه‌ای: غیرفعال",
    "👀 مشاهده مقادیر پیش‌فرض",
    "➕ تنظیم مقدار پیش‌فرض",
    "➖ حذف مقدار پیش‌فرض",
    "➕ افزودن ادمین",
    "➖ حذف ادمین",
    "👀 لیست ادمین‌ها",
    "🔧 تنظیم دسترسی ادمین‌ها",
    "✅ ایجاد پست",
    "❌ ایجاد پست",
    "✅ مدیریت امضاها",
    "❌ مدیریت امضاها",
    "✅ مدیریت متغیرها",
    "❌ مدیریت متغیرها",
    "✅ مقادیر پیش‌فرض",
    "❌ مقادیر پیش‌فرض",
    "✅ تنظیمات پیش‌فرض",
    "❌ تنظیمات پیش‌فرض",
    "✅ ثبت چنل",
    "❌ ثبت چنل",
    "✅ مدیریت تایمرها",
    "❌ مدیریت تایمرها",
    "✅ مدیریت اپشن‌ها",
    "❌ مدیریت اپشن‌ها",
    "✅ مدیریت ادمین‌ها",
    "❌ مدیریت ادمین‌ها",
    "🔙 بازگشت به مدیریت ادمین",
    "📤 اپلودر",
    "📣 ارسال همگانی",
    "⬆️ اپلود فایل",
    "✅ پایان اپلود",
    "🔙 بازگشت به اپلودر", 
    "🤖 ربات ساز",
    "👤 حساب کاربری",
    "🤖 هوش مصنوعی",
    "🛡️ امکانات اجباری"
]

# هندلر استارت برای خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    # ذخیره اطلاعات همه کاربران (حتی کاربران عادی)
    if str(user_id) not in data_store.user_data:
        data_store.user_data[str(user_id)] = {
            "first_name": message.from_user.first_name or "",
            "last_name": message.from_user.last_name or "",
            "username": message.from_user.username or "",
            "join_date": datetime.now().isoformat()
        }
        data_store.save_data()
    # اضافه کردن همه به لیست ارسال همگانی
    if user_id not in data_store.broadcast_users:
        data_store.broadcast_users.append(user_id)
        data_store.save_data()

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("file_"):
        file_uuid = args[1][5:]
        for priv_link, file_info in data_store.uploader_file_map.items():
            if file_info.get("uuid") == file_uuid and "channel_link" in file_info:
                ch_link = file_info["channel_link"]
                channel_username = ch_link.split("/")[3]
                msg_id = int(ch_link.split("/")[4])
                try:
                    msg = bot.forward_message(chat_id=user_id, from_chat_id=f"@{channel_username}", message_id=msg_id)
                    if msg.content_type == "document":
                        bot.send_document(user_id, msg.document.file_id)
                    elif msg.content_type == "photo":
                        bot.send_photo(user_id, msg.photo[-1].file_id)
                    elif msg.content_type == "video":
                        bot.send_video(user_id, msg.video.file_id)
                    else:
                        bot.send_message(user_id, "⚠️ فایل پشتیبانی نمی‌شود.")
                    try:
                        bot.delete_message(user_id, msg.message_id)
                    except Exception:
                        pass
                except Exception:
                    bot.send_message(user_id, "⚠️ خطا در ارسال فایل.")
                return
        bot.send_message(user_id, "⚠️ فایل مورد نظر وجود ندارد یا حذف شده است.")
        return

    user_name = message.from_user.first_name or ""
    status_text = data_store.state_messages.get(None, "وضعیت نامشخص")
    # اگر owner یا admin باشد منوی کامل
    if is_owner(user_id) or is_admin(user_id):
        markup = get_main_menu(user_id)
        welcome_text = data_store.settings["default_welcome"].format(name=user_name)
        data_store.last_user_message_id[user_id] = message.message_id
        msg = bot.send_message(user_id, f"{status_text}\n\n{welcome_text}", reply_markup=markup)
        data_store.last_message_id[user_id] = msg.message_id
    # کد جدید (فقط منوی ساده برای کاربر عادی)
    else:
        # کاربر عادی: منوی ساده با دو گزینه
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(types.KeyboardButton("👤 حساب کاربری"))
        markup.add(types.KeyboardButton(f"🤖 بات دستیار نسخه {BOT_VERSION}"))
        welcome_text = f"سلام {user_name} عزیز!\nبه ربات خوش آمدید 😊\nبرای استفاده بیشتر لطفاً با ادمین ارتباط بگیرید یا اطلاعات حساب کاربری و نسخه را ببینید."
        data_store.last_user_message_id[user_id] = message.message_id
        msg = bot.send_message(user_id, welcome_text, reply_markup=markup)
        data_store.last_message_id[user_id] = msg.message_id

def check_mandatory_requirements(user_id):
    # چک جوین اجباری
    for ch in data_store.mandatory_channels:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False, data_store.mandatory_join_message
        except Exception:
            return False, data_store.mandatory_join_message
    if data_store.mandatory_seen_channels:
        seen_cnt = data_store.user_data.get(str(user_id), {}).get("seen_count", 0)
        if seen_cnt < data_store.mandatory_seen_count:
            return False, data_store.mandatory_seen_message
    # ری‌اکشن هم مشابه بالا
    return True, ""

def check_mandatory_requirements(user_id):
    # چک جوین اجباری
    for ch in data_store.mandatory_channels:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False, data_store.mandatory_join_message
        except Exception:
            return False, data_store.mandatory_join_message
    if data_store.mandatory_seen_channels:
        seen_cnt = data_store.user_data.get(str(user_id), {}).get("seen_count", 0)
        if seen_cnt < data_store.mandatory_seen_count:
            return False, data_store.mandatory_seen_message
    # ری‌اکشن هم مشابه بالا
    return True, ""

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    ok, msg = check_mandatory_requirements(user_id)
    if not ok:
        bot.send_message(user_id, msg)
        return

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    ok, msg = check_mandatory_requirements(user_id)
    if not ok:
        bot.send_message(user_id, msg)
        return

# هندلر عکس برای دریافت تصاویر
@bot.message_handler(func=lambda m: data_store.get_user_state(m.from_user.id)["state"] == "post_with_signature_media", content_types=['photo', 'video'])
def handle_post_with_signature_media(message):
    user_id = message.from_user.id
    user_state = data_store.get_user_state(user_id)
    status_text = data_store.state_messages.get("post_with_signature_media", "در حال حاضر در حال ارسال رسانه برای پست هستید.")
    data_store.last_user_message_id[user_id] = message.message_id

    uploader_channel = data_store.uploader_channels[0] if data_store.uploader_channels else None
    if not uploader_channel:
        bot.send_message(user_id, "❗️ چنل اپلودری ثبت نشده است.", reply_markup=get_back_menu())
        return

    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        sent_message = bot.send_photo(uploader_channel, file_id)
        media_type = 'photo'
    elif message.content_type == 'video':
        file_id = message.video.file_id
        sent_message = bot.send_video(uploader_channel, file_id)
        media_type = 'video'
    else:
        return

    if "media_ids" not in user_state["data"]:
        user_state["data"]["media_ids"] = []
    # ذخیره اطلاعات کامل برای استفاده مجدد
    user_state["data"]["media_ids"].append({
        "type": media_type,
        "file_id": file_id,
        "uploader_msg_id": sent_message.message_id,
        "uploader_channel": uploader_channel
    })
    data_store.update_user_state(user_id, "post_with_signature_media", user_state["data"])

    # بلافاصله مدیا را به کاربر هم نمایش بده (پیش‌نمایش)
    try:
        if media_type == "photo":
            bot.send_photo(user_id, file_id, caption="پیش‌نمایش عکس دریافت شده (فایل ذخیره شد).")
        elif media_type == "video":
            bot.send_video(user_id, file_id, caption="پیش‌نمایش ویدیو دریافت شده (فایل ذخیره شد).")
    except Exception as e:
        logger.error(f"خطا در ارسال پیش‌نمایش مدیا به کاربر: {e}")

    try:
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n✅ فایل به چنل اپلودر ارسال شد و پیش‌نمایش داده شد.\n⏭️ برای ادامه، رسانه دیگری ارسال کنید یا گزینه مناسب را انتخاب کنید.",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                types.KeyboardButton("⏭️ پایان ارسال رسانه"),
                types.KeyboardButton("🔙 بازگشت به منوی اصلی")
            )
        )
        data_store.last_message_id[user_id] = msg.message_id
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {e}")
       
# فرمت کردن پست با قابلیت‌های متنی تلگرام
def format_post_content(post_content, variables):
    formatted_content = post_content
    for var, value in variables.items():
        var_format = data_store.controls.get(var, {}).get("format", "Simple")
        if var_format == "Link":
            # value = (text, url)
            text_part, url_part = value
            if text_part and url_part:
                formatted_content = formatted_content.replace(f"{{{var}}}", f'<a href="{url_part.strip()}">{text_part.strip()}</a>')
            else:
                formatted_content = formatted_content.replace(f"{{{var}}}", "")
        elif var_format == "Bold":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<b>{value}</b>")
        elif var_format == "BlockQuote":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<blockquote>{value}</blockquote>")
        elif var_format == "Italic":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<i>{value}</i>")
        elif var_format == "Code":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<code>{value}</code>")
        elif var_format == "Strike":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<s>{value}</s>")
        elif var_format == "Underline":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<u>{value}</u>")
        elif var_format == "Spoiler":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<tg-spoiler>{value}</tg-spoiler>")
        else:
            formatted_content = formatted_content.replace(f"{{{var}}}", value)
    return formatted_content

# پیش‌نمایش پست با کلیدهای شیشه‌ای و گزینه تایمر
# جدید: نمایش پیش‌نمایش و ارسال تایمردار با استفاده از file_id ثبت‌شده در media_ids (بدون نیاز به فایل دیسک)
def send_post_preview(user_id, post_content, media_ids=None, inline_buttons=None, row_width=4):
    markup_preview = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    continue_btn = types.KeyboardButton("✅ ادامه دادن")
    schedule_btn = types.KeyboardButton("⏰ زمان‌بندی پست")
    new_post_btn = types.KeyboardButton("🆕 پست جدید")
    main_menu_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup_preview.add(continue_btn)
    markup_preview.add(schedule_btn)
    markup_preview.add(new_post_btn)
    markup_preview.add(main_menu_btn)

    inline_keyboard = None
    if data_store.timer_settings.get("inline_buttons_enabled", True) and inline_buttons:
        inline_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        for button in inline_buttons:
            inline_keyboard.add(types.InlineKeyboardButton(button["text"], url=button["url"]))

    user_state = data_store.get_user_state(user_id)
    status_text = data_store.state_messages.get(user_state["state"], "وضعیت نامشخص")

    # نمایش پیش‌نمایش همه مدیاها با file_id ذخیره‌شده
    if media_ids:
        for media in media_ids:
            try:
                if media["type"] == "photo":
                    msg = bot.send_photo(user_id, media["file_id"], caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                elif media["type"] == "video":
                    msg = bot.send_video(user_id, media["file_id"], caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                data_store.last_message_id[user_id] = msg.message_id
            except Exception as e:
                logger.error(f"خطا در ارسال رسانه تلگرام با file_id: {e}")
    else:
        msg = bot.send_message(user_id, post_content, reply_markup=inline_keyboard, parse_mode="HTML")
        data_store.last_message_id[user_id] = msg.message_id

    try:
        bot.send_message(user_id, "📬 گزینه‌های پست:", reply_markup=markup_preview)
    except Exception as e:
        logger.error(f"خطا در ارسال منوی نهایی: {e}")

# در ارسال تایمردار هم دقیقا همین منطق:
def send_scheduled_post(job_id):
    if not data_store.timer_settings.get("timers_enabled", True):
        logger.info(f"تایمر {job_id} اجرا نشد چون تایمرها غیرفعال هستند.")
        return
    for post in data_store.scheduled_posts:
        if post["job_id"] == job_id:
            channel = post["channel"]
            post_content = post["post_content"]
            media_ids = post.get("media_ids", None)
            inline_buttons = post["inline_buttons"]
            row_width = post.get("row_width", 4)
            inline_keyboard = None
            if data_store.timer_settings.get("inline_buttons_enabled", True) and inline_buttons:
                inline_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
                for button in inline_buttons:
                    inline_keyboard.add(types.InlineKeyboardButton(button["text"], url=button["url"]))
            try:
                if media_ids:
                    for media in media_ids:
                        if media["type"] == "photo":
                            bot.send_photo(channel, media["file_id"], caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                        elif media["type"] == "video":
                            bot.send_video(channel, media["file_id"], caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                else:
                    bot.send_message(channel, post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                data_store.scheduled_posts.remove(post)
                data_store.save_data()
                schedule.clear(job_id)
            except Exception as e:
                logger.error(f"خطا در ارسال پست زمان‌بندی‌شده {job_id}: {e}")
            break
        
#=====================هلندر های اپلودر====================
@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "uploader_file_upload", content_types=['document', 'photo', 'video'])
def handle_uploader_files(message):
    user_id = message.from_user.id
    user_state = data_store.get_user_state(user_id)
    if "uploaded_files" not in user_state["data"]:
        user_state["data"]["uploaded_files"] = []
    # ذخیره فایل در لیست تا پایان آپلود
    user_state["data"]["uploaded_files"].append(message)
    data_store.update_user_state(user_id, "uploader_file_upload", user_state["data"])
    bot.send_message(user_id, "فایل دریافت شد! فایل دیگری بفرستید یا گزینه پایان اپلود را بزنید.", reply_markup=get_uploader_finish_menu())

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "uploader_menu" and message.text == "⬆️ اپلود فایل")
def start_uploader_file_upload(message):
    user_id = message.from_user.id
    data_store.update_user_state(user_id, "uploader_file_upload", {"uploaded_files": []})
    status_text = data_store.state_messages.get("uploader_file_upload")
    bot.send_message(user_id, f"{status_text}\n\nفایل(ها) را بفرستید. پس از اتمام، دکمه 'پایان اپلود' را بزنید.", reply_markup=get_uploader_finish_menu())
    
# این نسخه به‌روزرسانی شده و هماهنگ با ذخیره‌سازی اطلاعات دائمی uploader_file_map در فایل json جداگانه است.
@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "uploader_file_upload" and message.text == "✅ پایان اپلود")
def finish_uploader_file_upload(message):
    user_id = message.from_user.id
    user_state = data_store.get_user_state(user_id)
    uploaded_files = user_state["data"].get("uploaded_files", [])
    if not uploaded_files:
        bot.send_message(user_id, "❗️هیچ فایلی ارسال نشد. ابتدا فایل ارسال کنید.", reply_markup=get_uploader_finish_menu())
        return
    uploader_channel = data_store.uploader_channels[0] if data_store.uploader_channels else None
    if not uploader_channel:
        bot.send_message(user_id, "❗️چنل اپلودری ثبت نشده.", reply_markup=get_uploader_menu())
        return
    BOT_USERNAME = bot.get_me().username
    links_text = ""
    for file_msg in uploaded_files:
        if file_msg.content_type == "document":
            file_id = file_msg.document.file_id
            sent_message = bot.send_document(uploader_channel, file_id)
        elif file_msg.content_type == "photo":
            file_id = file_msg.photo[-1].file_id
            sent_message = bot.send_photo(uploader_channel, file_id)
        elif file_msg.content_type == "video":
            file_id = file_msg.video.file_id
            sent_message = bot.send_video(uploader_channel, file_id)
        else:
            continue
        ch_link = f"https://t.me/{uploader_channel[1:]}/{sent_message.message_id}"
        priv_uuid = str(uuid.uuid4())
        priv_link = f"https://t.me/{BOT_USERNAME}?start=file_{priv_uuid}"
        data_store.uploader_file_map[priv_link] = {
            "uuid": priv_uuid,
            "from_user": user_id,
            "file_type": file_msg.content_type,
            "date": datetime.now().isoformat(),
            "channel_link": ch_link,
            "start_link": priv_link
        }
        data_store.uploader_file_map[ch_link] = data_store.uploader_file_map[priv_link]
        links_text += priv_link + "\n"
    data_store.save_data()
    bot.send_message(user_id, f"✅ اپلود تمام شد!\n\nلینک خصوصی دانلود فایل(ها):\n{links_text.strip()}", reply_markup=get_uploader_menu())
    
@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "uploader_file_upload" and message.text == "🔙 بازگشت به اپلودر")
def back_to_uploader_menu(message):
    user_id = message.from_user.id
    data_store.update_user_state(user_id, "uploader_menu", {})
    bot.send_message(user_id, "📤 اپلودر:\nیکی از گزینه‌های زیر را انتخاب کنید.", reply_markup=get_uploader_menu())

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "uploader_menu" and message.text == "🛠️ ویرایش فایل")
def handle_edit_file_entry(message):
    user_id = message.from_user.id
    data_store.update_user_state(user_id, "edit_file_menu")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("✏️ ویرایش فایل"), types.KeyboardButton("🔗 ویرایش لینک"))
    markup.add(types.KeyboardButton("🔙 بازگشت به اپلودر"))
    bot.send_message(user_id, "یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "edit_file_menu")
def handle_edit_file_choice(message):
    user_id = message.from_user.id
    if message.text == "✏️ ویرایش فایل":
        data_store.update_user_state(user_id, "edit_file_wait_for_id")
        bot.send_message(user_id, "لینک فایل مورد نظر را بفرستید:", reply_markup=get_back_menu())
    elif message.text == "🔗 ویرایش لینک":
        data_store.update_user_state(user_id, "edit_link_wait_for_id")
        bot.send_message(user_id, "لینک فایل مورد نظر را بفرستید:", reply_markup=get_back_menu())

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "edit_file_wait_for_id")
def handle_edit_file_wait_for_id(message):
    user_id = message.from_user.id
    file_link = message.text.strip()
    if file_link not in data_store.uploader_file_map:
        bot.send_message(user_id, "لینک معتبر نیست یا پیدا نشد.", reply_markup=get_back_menu())
        return
    data_store.update_user_state(user_id, "edit_file_wait_for_new_file", {"editing_file_link": file_link})
    bot.send_message(user_id, "فایل جدید را بفرستید:", reply_markup=get_back_menu())

@bot.message_handler(content_types=['document', 'photo', 'video'], func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "edit_file_wait_for_new_file")
def handle_edit_file_upload_new(message):
    user_id = message.from_user.id
    user_state = data_store.get_user_state(user_id)
    file_link = user_state["data"].get("editing_file_link")
    # حذف mapping های قبلی
    old_info = data_store.uploader_file_map.pop(file_link, None)
    if old_info and "channel_link" in old_info:
        ch_link = old_info["channel_link"]
        if ch_link in data_store.uploader_file_map:
            del data_store.uploader_file_map[ch_link]
        try:
            channel_username = ch_link.split("/")[3]
            msg_id = int(ch_link.split("/")[4])
            uploader_channel = data_store.uploader_channels[0] if data_store.uploader_channels else None
            if uploader_channel:
                bot.delete_message(uploader_channel, msg_id)
        except Exception:
            pass
    uploader_channel = data_store.uploader_channels[0] if data_store.uploader_channels else None
    if not uploader_channel:
        bot.send_message(user_id, "❗️چنل اپلودری ثبت نشده.", reply_markup=get_uploader_menu())
        return
    BOT_USERNAME = bot.get_me().username
    if message.content_type == "document":
        file_id = message.document.file_id
        sent_message = bot.send_document(uploader_channel, file_id)
    elif message.content_type == "photo":
        file_id = message.photo[-1].file_id
        sent_message = bot.send_photo(uploader_channel, file_id)
    elif message.content_type == "video":
        file_id = message.video.file_id
        sent_message = bot.send_video(uploader_channel, file_id)
    else:
        bot.send_message(user_id, "نوع فایل پشتیبانی نمی‌شود.", reply_markup=get_back_menu())
        return
    ch_link = f"https://t.me/{uploader_channel[1:]}/{sent_message.message_id}"
    priv_uuid = str(uuid.uuid4())
    priv_link = f"https://t.me/{BOT_USERNAME}?start=file_{priv_uuid}"
    data_store.uploader_file_map[priv_link] = {
        "uuid": priv_uuid,
        "from_user": user_id,
        "file_type": message.content_type,
        "date": datetime.now().isoformat(),
        "channel_link": ch_link,
        "start_link": priv_link
    }
    data_store.uploader_file_map[ch_link] = data_store.uploader_file_map[priv_link]
    data_store.save_data()
    bot.send_message(user_id, f"فایل جدید ثبت شد!\nلینک خصوصی: {priv_link}", reply_markup=get_uploader_menu())
    data_store.update_user_state(user_id, "uploader_menu", {})
    
@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "edit_link_wait_for_id")
def handle_edit_link_wait_for_id(message):
    user_id = message.from_user.id
    file_link = message.text.strip()
    if file_link not in data_store.uploader_file_map:
        bot.send_message(user_id, "لینک معتبر نیست یا پیدا نشد.", reply_markup=get_back_menu())
        return
    old_info = data_store.uploader_file_map.pop(file_link)
    # فقط یک لینک خصوصی جدید ایجاد کن که فقط مخصوص ربات باشد، بدون هیچ پیام جدیدی در چنل اپلودر
    BOT_USERNAME = bot.get_me().username
    priv_uuid = str(uuid.uuid4())
    priv_link = f"https://t.me/{BOT_USERNAME}?start=file_{priv_uuid}"
    old_info["uuid"] = priv_uuid
    old_info["start_link"] = priv_link
    data_store.uploader_file_map[priv_link] = old_info
    # اگر لینک چنل در old_info هست، همان را نگه دار!
    if "channel_link" in old_info:
        data_store.uploader_file_map[old_info["channel_link"]] = old_info
    data_store.save_data()
    bot.send_message(user_id, f"لینک خصوصی جدید ساخته شد!\n{priv_link}", reply_markup=get_uploader_menu())
    data_store.update_user_state(user_id, "uploader_menu", {})

#======================هلندر های ارسال همگانی======================≠=

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "broadcast_choose_mode")
def handle_broadcast_choose_mode(message):
    user_id = message.from_user.id
    if message.text == "🗨️ ارسال با نقل قول":
        data_store.update_user_state(user_id, "broadcast_wait_for_message", {"broadcast_mode": "quote"})
        bot.send_message(user_id, "پیام خود را به همراه مدیا ارسال کنید (یا فوروارد کنید).", reply_markup=get_back_menu())
    elif message.text == "✉️ ارسال بدون نقل قول":
        data_store.update_user_state(user_id, "broadcast_wait_for_message", {"broadcast_mode": "noquote"})
        bot.send_message(user_id, "پیام خود را به همراه مدیا ارسال کنید (یا فوروارد کنید).", reply_markup=get_back_menu())
    elif message.text == "📢 ثبت چنل اپلودری":
        data_store.update_user_state(user_id, "register_uploader_channel")
        bot.send_message(user_id, "🖊️ آیدی چنل اپلودری را وارد کنید (مثال: @channelname):", reply_markup=get_back_menu())
    elif message.text == "🔙 بازگشت به منوی اصلی":
        data_store.reset_user_state(user_id)
        bot.send_message(user_id, "🏠 بازگشت به منوی اصلی:", reply_markup=get_main_menu(user_id))
    else:
        # منوی جدید با دکمه ثبت چنل اپلودری
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton("🗨️ ارسال با نقل قول"), types.KeyboardButton("✉️ ارسال بدون نقل قول"))
        markup.add(types.KeyboardButton("📢 ثبت چنل اپلودری"))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        bot.send_message(user_id, "یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=markup)
        
@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "broadcast_wait_for_message", content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation'])
def handle_broadcast_get_msg(message):
    user_id = message.from_user.id
    user_state = data_store.get_user_state(user_id)
    user_state["data"]["broadcast_message"] = message
    data_store.update_user_state(user_id, "broadcast_timer_or_instant", user_state["data"])
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("⏰ ارسال تایمردار"), types.KeyboardButton("🚀 ارسال فوری"))
    markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    if message.content_type == "text":
        bot.send_message(user_id, "پیام دریافت شد. ارسال به صورت فوری باشد یا تایمردار؟", reply_markup=markup)
    else:
        bot.send_message(user_id, "پیام مدیای شما دریافت شد. ارسال به صورت فوری باشد یا تایمردار؟", reply_markup=markup)

def send_broadcast_instant(requester_id, msg, mode):
    # لیست کامل کاربران بدون set و بدون محدودیت
    users = list(data_store.broadcast_users)
    # مطمئن شو خود درخواست‌کننده هم هست
    if requester_id not in users:
        users.append(requester_id)
    logging.info(f"لیست کاربران برای ارسال همگانی فوری: {users}")

    total = len(users)
    sent = 0
    progress_msg = bot.send_message(requester_id, "شروع ارسال... 0%")
    for i, uid in enumerate(users):
        try:
            logging.info(f"در حال ارسال به کاربر: {uid} - نوع: {msg.content_type}")
            if mode == "quote":
                bot.forward_message(uid, msg.chat.id, msg.message_id)
            else:  # noquote
                if msg.content_type == "text":
                    bot.send_message(uid, msg.text)
                elif msg.content_type == "photo":
                    bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption)
                elif msg.content_type == "video":
                    bot.send_video(uid, msg.video.file_id, caption=msg.caption)
                elif msg.content_type == "document":
                    bot.send_document(uid, msg.document.file_id, caption=msg.caption)
                elif msg.content_type == "audio":
                    bot.send_audio(uid, msg.audio.file_id, caption=msg.caption)
                elif msg.content_type == "voice":
                    bot.send_voice(uid, msg.voice.file_id)
                elif msg.content_type == "animation":
                    bot.send_animation(uid, msg.animation.file_id, caption=msg.caption)
                elif msg.content_type == "sticker":
                    bot.send_sticker(uid, msg.sticker.file_id)
                else:
                    bot.send_message(uid, "❗️ پیام متنی یا مدیا پشتیبانی نمی‌شود.")
            logging.info(f"ارسال موفق به کاربر: {uid}")
        except Exception as e:
            logging.error(f"خطا در ارسال برای کاربر {uid}: {e}")
            continue
        sent += 1
        try:
            percent = math.ceil(sent * 100 / total)
        except Exception:
            percent = 100
        if sent == total or sent % max(1, total // 20) == 0:
            try:
                bot.edit_message_text(f"ارسال درحال انجام ... {percent}%", requester_id, progress_msg.message_id)
            except Exception:
                pass
        time.sleep(0.5)
    try:
        bot.edit_message_text("✅ ارسال به همه کاربران تکمیل شد!", requester_id, progress_msg.message_id)
    except Exception:
        pass
        
def send_scheduled_broadcast(job_id):
    broadcasts_file = os.path.join('jsons', 'scheduled_broadcasts.json')
    if not os.path.exists(broadcasts_file):
        return
    try:
        with open(broadcasts_file, 'r', encoding='utf-8') as f:
            broadcasts = json.load(f)
        for bc in broadcasts:
            if bc["job_id"] == job_id:
                users = list(data_store.broadcast_users)  # بدون set یا محدودیت!
                logging.info(f"لیست کاربران برای ارسال همگانی تایمردار: {users}")
                if bc["broadcast_mode"] == "quote":
                    for uid in users:
                        try:
                            logging.info(f"در حال ارسال تایمردار با نقل قول به کاربر: {uid}")
                            bot.forward_message(uid, bc["uploader_channel"], bc["uploader_message_id"])
                        except Exception as e:
                            logging.error(f"خطا در ارسال تایمردار برای کاربر {uid}: {e}")
                    try:
                        bot.delete_message(bc["uploader_channel"], bc["uploader_message_id"])
                    except Exception:
                        pass
                else:
                    for uid in users:
                        try:
                            logging.info(f"در حال ارسال تایمردار بدون نقل قول به کاربر: {uid}")
                            bot.copy_message(uid, bc["uploader_channel"], bc["uploader_message_id"])
                        except Exception as e:
                            logging.error(f"خطا در ارسال تایمردار برای کاربر {uid}: {e}")
                    try:
                        bot.delete_message(bc["uploader_channel"], bc["uploader_message_id"])
                    except Exception:
                        pass
                broadcasts = [b for b in broadcasts if b["job_id"] != job_id]
                with open(broadcasts_file, 'w', encoding='utf-8') as f:
                    json.dump(broadcasts, f, ensure_ascii=False, indent=4)
                break
    except Exception as e:
        logger.error(f"خطا در ارسال scheduled broadcast: {e}")

@bot.message_handler(func=lambda message: data_store.get_user_state(message.from_user.id)["state"] == "broadcast_wait_for_timer")
def handle_broadcast_wait_for_timer(message):
    user_id = message.from_user.id
    user_state = data_store.get_user_state(user_id)
    try:
        time_str = message.text.strip()
        scheduled_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
        now = datetime.now()
        min_time = now + timedelta(minutes=5)
        example_time = (now + timedelta(minutes=5)).strftime("%Y/%m/%d %H:%M")
        if scheduled_time < min_time:
            bot.send_message(
                user_id,
                f"❗️ زمان باید متعلق به آینده باشد!\nباید در قالب yyyy/mm/dd hh:mm باشد.\nمثال:\n<code>{example_time}</code>",
                reply_markup=get_back_menu(),
                parse_mode="HTML"
            )
            return

        broadcast_mode = user_state["data"].get("broadcast_mode")
        broadcast_msg = user_state["data"].get("broadcast_message")
        uploader_channel = data_store.uploader_channels[0] if data_store.uploader_channels else None
        if not uploader_channel:
            bot.send_message(user_id, "❗️ هیچ چنل اپلودری ثبت نشده است.", reply_markup=get_main_menu(user_id))
            data_store.reset_user_state(user_id)
            return

        # ارسال پیام به چنل اپلودر و گرفتن پیام ذخیره شده
        if broadcast_mode == "quote":
            sent_message = bot.forward_message(uploader_channel, broadcast_msg.chat.id, broadcast_msg.message_id)
        else:  # noquote
            if broadcast_msg.content_type == "text":
                sent_message = bot.send_message(uploader_channel, broadcast_msg.text)
            elif broadcast_msg.content_type == "photo":
                sent_message = bot.send_photo(uploader_channel, broadcast_msg.photo[-1].file_id, caption=broadcast_msg.caption)
            elif broadcast_msg.content_type == "video":
                sent_message = bot.send_video(uploader_channel, broadcast_msg.video.file_id, caption=broadcast_msg.caption)
            elif broadcast_msg.content_type == "document":
                sent_message = bot.send_document(uploader_channel, broadcast_msg.document.file_id, caption=broadcast_msg.caption)
            elif broadcast_msg.content_type == "audio":
                sent_message = bot.send_audio(uploader_channel, broadcast_msg.audio.file_id, caption=broadcast_msg.caption)
            elif broadcast_msg.content_type == "voice":
                sent_message = bot.send_voice(uploader_channel, broadcast_msg.voice.file_id)
            elif broadcast_msg.content_type == "animation":
                sent_message = bot.send_animation(uploader_channel, broadcast_msg.animation.file_id, caption=broadcast_msg.caption)
            elif broadcast_msg.content_type == "sticker":
                sent_message = bot.send_sticker(uploader_channel, broadcast_msg.sticker.file_id)
            else:
                sent_message = bot.send_message(uploader_channel, "❗️ پیام متنی یا مدیا پشتیبانی نمی‌شود.")

        # ذخیره شناسه و لینک پیام اپلودر
        post_uuid = str(uuid.uuid4())
        ch_link = f"https://t.me/{uploader_channel[1:]}/{sent_message.message_id}"
        data_store.scheduled_broadcasts.append({
            "job_id": post_uuid,
            "requester_id": user_id,
            "time": time_str,
            "broadcast_mode": broadcast_mode,
            "uploader_channel": uploader_channel,
            "uploader_message_id": sent_message.message_id,
            "uploader_link": ch_link,
            "content_type": broadcast_msg.content_type
        })
        data_store.save_data()
        schedule.every().day.at(scheduled_time.strftime("%H:%M")).do(send_scheduled_broadcast, job_id=post_uuid).tag(post_uuid)
        bot.send_message(user_id, f"✅ پیام شما برای ارسال همگانی در زمان {time_str} ذخیره شد.", reply_markup=get_main_menu(user_id))
        data_store.reset_user_state(user_id)
    except Exception as e:
        now = datetime.now()
        example = (now + timedelta(minutes=5)).strftime("%Y/%m/%d %H:%M")
        bot.send_message(
            user_id,
            f"❗️ فرمت زمان اشتباه است!\n باید از زمان اینده باشد \n باید در قالب yyyy/mm/dd hh:mm باشد.\nمثال:\n<code>{example}</code>",
            reply_markup=get_back_menu(),
            parse_mode="HTML"
        )
#==========================هلندر ربات ساز و حساب کاربری=======================

@bot.message_handler(func=lambda m: m.text == "🤖 ربات ساز")
def handle_bot_creator(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    bot.send_message(user_id, "آیدی عددی مالک ربات جدید را وارد کنید:", reply_markup=get_main_menu(user_id))
    data_store.update_user_state(user_id, "wait_for_new_owner_id")

@bot.message_handler(func=lambda m: data_store.get_user_state(m.from_user.id)["state"] == "wait_for_new_owner_id")
def handle_new_owner_id(message):
    user_id = message.from_user.id
    try:
        new_owner_id = int(message.text.strip())
        data_store.update_user_state(user_id, "wait_for_new_bot_token", {"new_owner_id": new_owner_id})
        bot.send_message(user_id, "کد API ربات جدید را وارد کنید:", reply_markup=get_main_menu(user_id))
    except:
        bot.send_message(user_id, "آیدی عددی معتبر وارد کنید:", reply_markup=get_main_menu(user_id))

@bot.message_handler(func=lambda m: data_store.get_user_state(m.from_user.id)["state"] == "wait_for_new_bot_token")
def handle_new_bot_token(message):
    user_id = message.from_user.id
    api_token = message.text.strip()
    new_owner_id = data_store.get_user_state(user_id)["data"].get("new_owner_id", user_id)
    data_store.update_user_state(user_id, "wait_for_bot_child_name", {"new_owner_id": new_owner_id, "api_token": api_token})
    bot.send_message(user_id, "یک نام (ایدی عددی یا یوزرنیم) برای ربات بچه انتخاب کنید:", reply_markup=get_main_menu(user_id))

@bot.message_handler(func=lambda m: data_store.get_user_state(m.from_user.id)["state"] == "wait_for_bot_child_name")
def handle_new_bot_child_name(message):
    user_id = message.from_user.id
    child_name = message.text.strip()
    st = data_store.get_user_state(user_id)
    api_token = st["data"]["api_token"]
    new_owner_id = st["data"]["new_owner_id"]
    bot_folder = f"bot_{user_id}_{int(time.time())}"
    os.makedirs(bot_folder, exist_ok=True)
    with open("baby_bot.py", "r", encoding="utf-8") as f:
        template_code = f.read()
    BOT_TEMPLATE = safe_format(
        template_code,
        API_TOKEN=api_token,
        OWNER_USER=new_owner_id,
        BOT_VERSION=BOT_VERSION,
        BOT_CHILD_NAME=child_name
    )
    bot_file_path = os.path.join(bot_folder, "bot.py")
    with open(bot_file_path, "w", encoding="utf-8") as f:
        f.write(BOT_TEMPLATE)
    config_path = os.path.join(bot_folder, "config.json")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({
                "API_TOKEN": api_token,
                "OWNER_USER": new_owner_id,
                "BOT_CHILD_NAME": child_name
            }, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"config.json written in: {config_path}")
        print(f"Exists? {os.path.exists(config_path)}")
    data_store.update_user_state(user_id, "ask_run_created_bot", {"bot_file_path": "bot.py", "bot_folder": bot_folder})
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("✅ بله"))
    bot.send_message(
        user_id,
        f"✅ ربات جدید ساخته شد و نام آن <code>{child_name}</code> است.\n\nآیا مایل هستید ربات ساخته‌شده فوراً ران شود؟",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda m: data_store.get_user_state(m.from_user.id)["state"] == "ask_run_created_bot" and m.text == "✅ بله")
def handle_run_created_bot(message):
    user_id = message.from_user.id
    user_state = data_store.get_user_state(user_id)
    bot_file_path = user_state['data'].get('bot_file_path', 'bot.py')
    bot_folder = user_state['data'].get('bot_folder')
    try:
        proc = subprocess.Popen(
            ["python3", "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=bot_folder
        )
        time.sleep(2)
        retcode = proc.poll()
        if retcode is not None and retcode != 0:
            out, err = proc.communicate(timeout=5)
            error_msg = err.decode('utf-8') if err else "خطای نامشخص"
            bot.send_message(user_id, f"❌ اجرای ربات با خطا مواجه شد:\n<code>{error_msg}</code>", parse_mode="HTML")
        else:
            bot.send_message(user_id, "✅ ربات ساخته‌شده با موفقیت اجرا شد.", reply_markup=get_main_menu(user_id))
        data_store.reset_user_state(user_id)
    except Exception as ex:
        bot.send_message(user_id, f"❌ اجرای ربات جدید با خطا مواجه شد:\n<code>{str(ex)}</code>", parse_mode="HTML")
        data_store.reset_user_state(user_id)

@bot.message_handler(func=lambda m: m.text == "👤 حساب کاربری")
def handle_user_account(message):
    user_id = message.from_user.id
    user_info = data_store.user_data.get(str(user_id), {})
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    username = user_info.get("username", "")
    join_date = user_info.get("join_date", "")

    # اگر owner یا admin است، آمار کامل و امکانات بیشتر
    if is_owner(user_id) or is_admin(user_id):
        now = datetime.now()
        total_count = len(data_store.user_data)
        active_count = sum(
            1 for u in data_store.user_data.values()
            if (now - datetime.fromisoformat(u.get("last_seen", u.get("join_date", now.isoformat())))).days <= 31
        )
        week_count = sum(
            1 for u in data_store.user_data.values()
            if (now - datetime.fromisoformat(u.get("join_date", now.isoformat()))).days < 7
        )
        month_count = sum(
            1 for u in data_store.user_data.values()
            if (now - datetime.fromisoformat(u.get("join_date", now.isoformat()))).days < 31
        )
        year_count = sum(
            1 for u in data_store.user_data.values()
            if datetime.fromisoformat(u.get("join_date", now.isoformat())).year == now.year
        )
        text = (
            "ℹ️ <b>اطلاعات حساب کاربری ادمین/اونر:</b>\n\n"
            "<blockquote>"
            f"👤 نام: <b>{first_name}</b>\n"
            f"👥 نام خانوادگی: <b>{last_name}</b>\n"
            f"🔗 یوزرنیم: <a href='https://t.me/{username}'>{username}</a>\n"
            f"🆔 آیدی عددی: <code>{user_id}</code>\n"
            f"🕓 تاریخ عضویت: <code>{join_date[:10]} {join_date[11:16]}</code>\n"
            "</blockquote>\n"
            "👥 <b>آمار عضویت کل بات:</b>\n"
            f"<blockquote>کل اعضا: <b>{total_count}</b>\n"
            f"اعضای فعال: <b>{active_count}</b>\n"
            f"اعضای هفته اخیر: <b>{week_count}</b>\n"
            f"اعضای ماه اخیر: <b>{month_count}</b>\n"
            f"اعضای امسال: <b>{year_count}</b></blockquote>\n"
        )
    else:
        # کاربر عادی: فقط اطلاعات خودش
        text = (
            "ℹ️ <b>اطلاعات حساب کاربری شما:</b>\n\n"
            "<blockquote>"
            f"👤 نام: <b>{first_name}</b>\n"
            f"👥 نام خانوادگی: <b>{last_name}</b>\n"
            f"🔗 یوزرنیم: <a href='https://t.me/{username}'>{username}</a>\n"
            f"🆔 آیدی عددی: <code>{user_id}</code>\n"
            f"🕓 تاریخ عضویت: <code>{join_date[:10]} {join_date[11:16]}</code>\n"
            "</blockquote>\n"
            "برای امکانات بیشتر لطفاً با ادمین بات ارتباط بگیرید."
        )
    
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(types.KeyboardButton("👤 حساب کاربری"))
        markup.add(types.KeyboardButton(f"🤖 بات دستیار نسخه {BOT_VERSION}"))
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)
        
def get_child_files_info(user_id):
    base = "."  # یا مسیر اصلی هاست بچه‌ها
    user_files_count = 0
    user_files_size = 0
    for folder in os.listdir(base):
        if folder.startswith("bot_") and os.path.isdir(folder):
            json_path = os.path.join(base, folder, "central_data", "uploader_files.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    files = json.load(f)
                for fileinfo in files.values():
                    if fileinfo.get("from_user") == user_id:
                        user_files_count += 1
                        # اگر حجم داری حساب کن
                        # می‌تونی اینجا مسیر فایل رو پیدا کنی و با os.path.getsize حساب کنی
    return user_files_count, user_files_size

    user_files_count, user_files_size = get_child_files_info(user_id)
    user_files_size_mb = user_files_size / (1024*1024)

#==========================هلندر هوش مصنوعی=======================

import re
import requests
from collections import defaultdict, deque

# حافظه مکالمه برای هر کاربر (آخرین 8 پیام)
conversation_memory = defaultdict(lambda: deque(maxlen=8))

def web_search(query):
    """جستجوی ساده وب در DuckDuckGo (بدون API)"""
    try:
        url = f"https://duckduckgo.com/html/?q={query}"
        resp = requests.get(url, timeout=10)
        titles = re.findall(r'<a rel="nofollow" class="result__a" href="[^"]+">([^<]+)</a>', resp.text)
        if titles:
            return f"🔎 نتیجه وب: {titles[0]}"
        else:
            return "🌐 نتیجه خاصی پیدا نشد!"
    except Exception:
        return "❌ خطا در جستجوی وب!"

def calculator(expr):
    """ماشین حساب ساده فقط برای عملیات ریاضی ابتدایی"""
    try:
        result = eval(expr, {"__builtins__": None})
        return f"🧮 جواب: {result}"
    except Exception:
        return "فرمت عبارت ریاضی اشتباهه!"

def summarize_history(history):
    """خلاصه مکالمه اخیر کاربر"""
    summary = ""
    for i, (msg, resp) in enumerate(history):
        summary += f"👤 {msg}\n🤖 {resp}\n"
    return summary.strip()

def ai_brain(user_id, user_input):
    t = user_input.strip().lower()
    hist = conversation_memory[user_id]

    # رفتار مکالمه‌ای و تحلیلی با حافظه
    if len(hist) > 0 and (
        "این یعنی چی" in t or "تحلیل کن" in t or "بعدش چی شد" in t or "توضیح بده" in t):
        prev_msg, prev_resp = hist[-1]
        return (
            f"در پیام قبلی پرسیدی: «{prev_msg}»\n"
            f"پاسخ من این بود: «{prev_resp}»\n"
            "اگر بیشتر توضیح می‌خوای، سوال خودت رو دقیق‌تر بپرس یا بگو دقیق‌تر تحلیل کنم."
        )

    # سلام و احوالپرسی هوشمند
    if t in ["سلام", "درود", "hi", "hello"]:
        return "سلام دوست من! چطور کمکت کنم؟ هر سوالی داری بپرس، هم حساب می‌کنم، هم تحلیل و هم سرچ می‌کنم 😉"

    # ماشین حساب
    if re.match(r"^[\d\+\-\*/\s\(\)\.]+$", t):
        return calculator(t)

    # تخیل و داستان‌گویی
    if "داستان" in t or "تخیل" in t or "یک داستان بگو" in t:
        return (
            "روزی روزگاری یک ربات ایرانی به نام 'مغز زرنگ' بود که باهوش‌تر از همه انسان‌ها شد... "
            "او می‌توانست به همه سوال‌های جهان جواب بدهد و همیشه دوست داشتنی و خندان بود!"
        )

    # سوال علمی، خبری یا تحلیلی
    if any(word in t for word in [
        "چیست", "کیست", "خبر", "چگونه", "چطور", "کجاست", "چه کسی", "چرا", "تحلیل"
    ]):
        result = web_search(user_input)
        return (
            f"{result}\n\n"
            "اگر توضیح بیشتری خواستی بپرس: «این یعنی چی؟» یا «تحلیل کن»"
        )

    # جمع‌بندی مکالمه
    if "جمع‌بندی" in t or "خلاصه کن" in t or "همه چی رو خلاصه کن" in t:
        return summarize_history(hist)

    # جواب پیش‌فرض انسانی و شوخ
    return (
        "من مغز هوشمندتم! سوالتو واضح‌تر بپرس یا بگو ماشین حساب، داستان یا جستجو کنم. "
        "همیشه آماده‌ام تحلیل کنم یا حتی باهات شوخی کنم 😎"
    )

# === هندلر بات ===

@bot.message_handler(func=lambda m: m.text == "🤖 هوش مصنوعی")
def handle_ai(message):
    user_id = message.from_user.id
    bot.send_message(
        user_id,
        "✍️ هر سوالی داری بپرس! من هوش مصنوعی مغز زرنگ هستم؛ مکالمه رو یادم می‌مونه، تحلیل می‌کنم، سرچ می‌کنم، ماشین حساب و داستان‌گو هم هستم."
    )
    data_store.update_user_state(user_id, "ai_wait_for_input")

@bot.message_handler(func=lambda m: data_store.get_user_state(m.from_user.id)["state"] == "ai_wait_for_input")
def ai_answer(message):
    user_id = message.from_user.id
    prompt = message.text.strip()

    # مغز هوش مصنوعی (با حافظه مکالمه)
    answer = ai_brain(user_id, prompt)
    conversation_memory[user_id].append((prompt, answer))

    bot.send_message(user_id, f"🤖 پاسخ:\n\n{answer}", reply_markup=get_main_menu(user_id))
    data_store.reset_user_state(user_id)
    
#==========================هلندر پیام ها=======================

# پردازش پیام‌ها
@bot.message_handler(func=lambda message: True)
def process_message(message):
    user_id = message.from_user.id
    text = message.text
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    logger.info(f"پیام دریافت‌شده از {user_id}: '{text}'، حالت: {state}")
    # ذخیره آیدی پیام کاربر
    data_store.last_user_message_id[user_id] = message.message_id
    
    if text in MAIN_MENU_BUTTONS:
            logger.info(f"دکمه منو شناسایی شد: {text}")
            if process_main_menu_button(user_id, text):
                return

    if state in ["admin_management", "add_admin", "remove_admin", "select_admin_for_permissions", "manage_admin_permissions"]:
        logger.info(f"هدایت پیام به handle_admin_management، حالت: {state}")
        handle_admin_management(user_id, text)
        return

        if state == "admin_management":
            handle_admin_management(user_id, text)
            return
        
    if state == "default_values_management":
        logger.info(f"هدایت پیام به handle_default_values_management، حالت: {state}")
        handle_default_values_management(user_id, text)
        return

    if state == "timer_inline_management":
        logger.info(f"پردازش پیام در timer_inline_management، متن: {text}")
        timers_enabled = data_store.timer_settings.get("timers_enabled", True)
        inline_buttons_enabled = data_store.timer_settings.get("inline_buttons_enabled", True)
        timers_status = "✅ فعال" if timers_enabled else "❌ غیرفعال"
        buttons_status = "✅ فعال" if inline_buttons_enabled else "❌ غیرفعال"
        status_message = (
            f"{status_text}\n\n"
            f"⏰ وضعیت تایمرها: {timers_status}\n"
            f"🔗 وضعیت کلیدهای شیشه‌ای: {buttons_status}\n\n"
            f"✨ مدیریت اپشن‌ها:"
        )
        
        timers_btn_text = "✅ تایمرها: فعال" if timers_enabled else "❌ تایمرها: غیرفعال"
        inline_buttons_btn_text = "✅ کلیدهای شیشه‌ای: فعال" if inline_buttons_enabled else "❌ کلیدهای شیشه‌ای: غیرفعال"
        
        if text == timers_btn_text:
            data_store.timer_settings["timers_enabled"] = not timers_enabled
            data_store.save_data()
            new_timers_status = "✅ فعال" if not timers_enabled else "❌ غیرفعال"
            action_text = "فعال شدند" if not timers_enabled else "غیرفعال شدند"
            try:
                bot.edit_message_text(
                    chat_id=user_id, 
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⏰ تایمرها {action_text}.\n⏰ وضعیت تایمرها: {new_timers_status}\n🔗 وضعیت کلیدهای شیشه‌ای: {buttons_status}\n\n✨ مدیریت اپشن‌ها:",
                    reply_markup=get_timer_inline_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⏰ تایمرها {action_text}.\n⏰ وضعیت تایمرها: {new_timers_status}\n🔗 وضعیت کلیدهای شیشه‌ای: {buttons_status}\n\n✨ مدیریت اپشن‌ها:", reply_markup=get_timer_inline_menu())
                data_store.last_message_id[user_id] = msg.message_id
        elif text == inline_buttons_btn_text:
            data_store.timer_settings["inline_buttons_enabled"] = not inline_buttons_enabled
            data_store.save_data()
            new_buttons_status = "✅ فعال" if not inline_buttons_enabled else "❌ غیرفعال"
            action_text = "فعال شدند" if not inline_buttons_enabled else "غیرفعال شدند"
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🔗 کلیدهای شیشه‌ای {action_text}.\n⏰ وضعیت تایمرها: {timers_status}\n🔗 وضعیت کلیدهای شیشه‌ای: {new_buttons_status}\n\n✨ مدیریت اپشن‌ها:",
                    reply_markup=get_timer_inline_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🔗 کلیدهای شیشه‌ای {action_text}.\n⏰ وضعیت تایمرها: {timers_status}\n🔗 وضعیت کلیدهای شیشه‌ای: {new_buttons_status}\n\n✨ مدیریت اپشن‌ها:", reply_markup=get_timer_inline_menu())
                data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state is None:
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n🔍 لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🔍 لطفاً یکی از گزینه‌های منو را انتخاب کنید.", reply_markup=get_main_menu(user_id))
            data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state == "signature_management":
        handle_signature_management(user_id, text)
        return
    
    if state == "select_signature":
        if text in data_store.signatures:
            data_store.update_user_state(user_id, "post_with_signature_media", {"signature_name": text})
            markup = get_back_menu()
            markup.add(types.KeyboardButton("⏭️ رد کردن مرحله رسانه"))
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n📸 عکس یا ویدیو ارسال کنید (یا دکمه زیر برای رد کردن):",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n📸 عکس یا ویدیو ارسال کنید (یا دکمه زیر برای رد کردن):", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state == "post_with_signature_media":
        if text == "⏭️ پایان ارسال رسانه" or text == "⏭️ رد کردن مرحله رسانه":
            media_paths = user_state["data"].get("media_paths", None)
            data_store.update_user_state(user_id, "post_with_signature_values", {"media_paths": media_paths, "current_var_index": 0})
            sig_name = user_state["data"]["signature_name"]
            signature = data_store.signatures[sig_name]
            variables = signature["variables"]
            
            # مقداردهی اولیه برای متغیرها با استفاده از مقادیر پیش‌فرض
            user_state["data"]["temp_post_content"] = signature["template"]
            variables_without_default = []
            for var in variables:
                if var in data_store.default_values:
                    user_state["data"][var] = data_store.default_values[var]
                else:
                    user_state["data"][var] = f"[{var} وارد نشده]"
                    variables_without_default.append(var)
            
            data_store.update_user_state(user_id, "post_with_signature_values", {
                "media_paths": media_paths,
                "current_var_index": 0,
                "variables_without_default": variables_without_default
            })
            
            if variables_without_default:
                # نمایش اولیه پست
                temp_content = user_state["data"]["temp_post_content"]
                for var in variables:
                    temp_content = temp_content.replace(f"{{{var}}}", user_state["data"][var])
                display_text = f"{status_text}\n\n📝 در حال ساخت پست:\n\n{temp_content}\n\nـــــــــــــــــــــ\n🖊️ مقدار {variables_without_default[0]} را وارد کنید:"
                
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=display_text,
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, display_text, reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            else:
                post_content = signature["template"]
                for var in variables:
                    post_content = post_content.replace(f"{{{var}}}", user_state["data"][var])
                data_store.update_user_state(user_id, "add_inline_buttons", {"post_content": post_content, "media_paths": media_paths})
                markup = get_back_menu()
                markup.add(types.KeyboardButton("✅ پایان افزودن کلیدها"))
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n🔗 کلید شیشه‌ای اضافه کنید (نام کلید و لینک را به‌صورت 'نام|لینک' وارد کنید) یا 'پایان افزودن کلیدها' را بزنید:",
                        reply_markup=markup
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n🔗 کلید شیشه‌ای اضافه کنید (نام کلید و لینک را به‌صورت 'نام|لینک' وارد کنید) یا 'پایان افزودن کلیدها' را بزنید:", reply_markup=markup)
                    data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state == "post_with_signature_values":
        sig_name = user_state["data"]["signature_name"]
        current_index = user_state["data"].get("current_var_index", 0)
        signature = data_store.signatures[sig_name]
        variables_without_default = user_state["data"].get("variables_without_default", signature["variables"])
        
        # جدید (اصلاح‌شده و کاملاً پایدار)
        var_name = variables_without_default[current_index]
        
        if user_state["data"].get('Link_url_mode', False):
            link_var_name = user_state["data"]['current_link_var']
            user_state["data"][f"{link_var_name}_url"] = text
            user_state["data"]['Link_url_mode'] = False
            user_state["data"][link_var_name] = "done"
            current_index += 1
        else:
            var_format = data_store.controls.get(var_name, {}).get("format", "Simple")
            if var_format == "Link":
                user_state["data"][f"{var_name}_text"] = text
                user_state["data"]['Link_url_mode'] = True
                user_state["data"]['current_link_var'] = var_name
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n📝 حالا آدرس لینک {var_name} را وارد کن:",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n📝 حالا آدرس لینک {var_name} را وارد کن:", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                return
            else:
                user_state["data"][var_name] = text
                current_index += 1
        
        if current_index < len(variables_without_default):
            data_store.update_user_state(user_id, None, {"current_var_index": current_index})
            
            # به‌روزرسانی محتوای پست
            temp_content = user_state["data"]["temp_post_content"]
            for var in signature["variables"]:
                temp_content = temp_content.replace(f"{{{var}}}", user_state["data"][var])
            display_text = f"{status_text}\n\n📝 در حال ساخت پست:\n\n{temp_content}\n\nـــــــــــــــــــــ\n🖊️ مقدار {variables_without_default[current_index]} را وارد کنید:"
            
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=display_text,
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, display_text, reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            # جدید (برای هر متغیر Link، مقدار متن و url را ترکیب می‌کند و به صورت tuple می‌دهد)
            variables_dict = {}
            for var in signature["variables"]:
                var_format = data_store.controls.get(var, {}).get("format", "Simple")
                if var_format == "Link":
                    text_part = user_state["data"].get(f"{var}_text", "")
                    url_part = user_state["data"].get(f"{var}_url", "")
                    variables_dict[var] = (text_part, url_part)
                else:
                    variables_dict[var] = user_state["data"][var]
            result = format_post_content(signature["template"], variables_dict)
            
            media_paths = user_state["data"].get("media_paths")
            data_store.update_user_state(user_id, "ask_for_inline_buttons", {"post_content": result, "media_paths": media_paths, "inline_buttons": []})
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(types.KeyboardButton("✅ بله"), types.KeyboardButton("❌ خیر"))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🔗 آیا می‌خواهید کلید شیشه‌ای اضافه کنید؟",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🔗 آیا می‌خواهید کلید شیشه‌ای اضافه کنید؟", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state == "ask_for_inline_buttons":
        if text == "✅ بله":
            data_store.update_user_state(user_id, "add_inline_button_name", {"inline_buttons": user_state["data"].get("inline_buttons", []), "row_width": 4})
            markup = get_back_menu()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n📝 نام کلید شیشه‌ای را وارد کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n📝 نام کلید شیشه‌ای را وارد کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        elif text == "❌ خیر":
            post_content = user_state["data"].get("post_content", "")
            media_ids = user_state["data"].get("media_ids", None)
            media_paths = user_state["data"].get("media_paths", [])
            inline_buttons = user_state["data"].get("inline_buttons", [])
            data_store.update_user_state(user_id, "post_with_signature_ready", {
                "post_content": post_content,
                "media_ids": media_ids,
                "media_paths": media_paths,
                "inline_buttons": inline_buttons,
                "row_width": 4
            })
            media_ids = user_state["data"].get("media_ids", None)
            media_paths = user_state["data"].get("media_paths", None)
            send_post_preview(user_id, post_content, media_ids or media_paths, inline_buttons, row_width=4)
        return
    
    if state == "add_inline_button_name":
        button_text = text.strip()
        if button_text:
            data_store.update_user_state(user_id, "add_inline_button_url", {
                "inline_buttons": user_state["data"].get("inline_buttons", []),
                "row_width": user_state["data"].get("row_width", 4),
                "button_text": button_text
            })
            markup = get_back_menu()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🔗 لینک کلید '{button_text}' را وارد کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🔗 لینک کلید '{button_text}' را وارد کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ نام کلید نمی‌تواند خالی باشد! لطفاً یک نام وارد کنید:",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ نام کلید نمی‌تواند خالی باشد! لطفاً یک نام وارد کنید:", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        return
        
    if state == "add_inline_button_url":
        button_url = text.strip()
        if button_url:
            button_text = user_state["data"].get("button_text", "")
            inline_buttons = user_state["data"].get("inline_buttons", [])
            inline_buttons.append({"text": button_text, "url": button_url})
            
            data_store.update_user_state(user_id, "ask_continue_adding_buttons", {"inline_buttons": inline_buttons})
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(types.KeyboardButton("✅ ادامه دادن"), types.KeyboardButton("❌ خیر"))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ کلید '{button_text}' اضافه شد. آیا می‌خواهید کلید دیگری اضافه کنید؟",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ کلید '{button_text}' اضافه شد. آیا می‌خواهید کلید دیگری اضافه کنید؟", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ لینک نمی‌تواند خالی باشد! لطفاً یک لینک معتبر وارد کنید:",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لینک نمی‌تواند خالی باشد! لطفاً یک لینک معتبر وارد کنید:", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state == "ask_continue_adding_buttons":
        if text == "✅ ادامه دادن":
            data_store.update_user_state(user_id, "select_button_position")
            markup = get_button_layout_menu()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n📏 نحوه نمایش کلید شیشه‌ای بعدی را انتخاب کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n📏 نحوه نمایش کلید شیشه‌ای بعدی را انتخاب کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        elif text == "❌ خیر":
            post_content = user_state["data"].get("post_content", "")
            media_paths = user_state["data"].get("media_paths", [])
            inline_buttons = user_state["data"].get("inline_buttons", [])
            data_store.update_user_state(user_id, "post_with_signature_ready", {
                "post_content": post_content,
                "media_paths": media_paths,
                "inline_buttons": inline_buttons,
                "row_width": 4
            })
            send_post_preview(user_id, post_content, media_paths, inline_buttons, row_width=4)
        return
    
    if state == "select_button_position":
        row_width = 4  # کنار هم (به صورت پیش‌فرض)
        if text == "📏 به کنار":
            row_width = 4  # کنار هم
        elif text == "📐 به پایین":
            row_width = 1  # زیر هم
        
        data_store.update_user_state(user_id, "add_inline_button_name", {
            "inline_buttons": user_state["data"].get("inline_buttons", []),
            "row_width": row_width
        })
        markup = get_back_menu()
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n📝 نام کلید شیشه‌ای بعدی را وارد کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n📝 نام کلید شیشه‌ای بعدی را وارد کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
        return

    if state == "post_with_signature_ready":
        if text == "✅ ادامه دادن":
            if not data_store.channels:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ هیچ چنلی ثبت نشده است. ابتدا یک چنل ثبت کنید.",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ چنلی ثبت نشده است. ابتدا یک چنل ثبت کنید.", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                return
            
            # نمایش لیست چنل‌ها برای انتخاب
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for channel in data_store.channels:
                markup.add(types.KeyboardButton(channel))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            data_store.update_user_state(user_id, "select_channel_for_post", {
                "post_content": user_state["data"].get("post_content", ""),
                "media_paths": user_state["data"].get("media_paths", []),
                "inline_buttons": user_state["data"].get("inline_buttons", []),
                "row_width": user_state["data"].get("row_width", 4)
            })
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n📢 چنل مقصد را انتخاب کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n📢 چنل مقصد را انتخاب کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
            return
    
    if state == "select_channel_for_post":
        if text in data_store.channels:
            post_content = user_state["data"].get("post_content", "")
            media_paths = user_state["data"].get("media_paths", [])
            inline_buttons = user_state["data"].get("inline_buttons", [])
            row_width = user_state["data"].get("row_width", 4)
            channel = text
            
            inline_keyboard = None
            if data_store.timer_settings.get("inline_buttons_enabled", True) and inline_buttons:
                inline_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
                for button in inline_buttons:
                    inline_keyboard.add(types.InlineKeyboardButton(button["text"], url=button["url"]))
            
            if media_paths:
                for media in media_paths:
                    try:
                        with open(media["path"], "rb") as file:
                            if media["type"] == "photo":
                                bot.send_photo(user_id, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                            elif media["type"] == "video":
                                bot.send_video(user_id, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                    except Exception as e:
                        logger.error(f"خطا در ارسال رسانه: {e}")
                        try:
                            bot.edit_message_text(
                                chat_id=user_id,
                                message_id=data_store.last_message_id[user_id],
                                text=f"{status_text}\n\n⚠️ خطا در ارسال رسانه: {e}",
                                reply_markup=get_main_menu(user_id)
                            )
                        except Exception as e:
                            logger.error(f"خطا در ویرایش پیام: {e}")
                            msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ارسال رسانه: {e}", reply_markup=get_main_menu(user_id))
                            data_store.last_message_id[user_id] = msg.message_id
                        data_store.reset_user_state(user_id)
                        return
            else:
                try:
                    bot.send_message(channel, post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"خطا در ارسال پیام: {e}")
                    try:
                        bot.edit_message_text(
                            chat_id=user_id,
                            message_id=data_store.last_message_id[user_id],
                            text=f"{status_text}\n\n⚠️ خطا در ارسال پیام: {e}",
                            reply_markup=get_main_menu(user_id)
                        )
                    except Exception as e:
                        logger.error(f"خطا در ویرایش پیام: {e}")
                        msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ارسال پیام: {e}", reply_markup=get_main_menu(user_id))
                        data_store.last_message_id[user_id] = msg.message_id
                    data_store.reset_user_state(user_id)
                    return
            
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ پست با موفقیت به {channel} ارسال شد.\n🏠 منوی اصلی:",
                    reply_markup=get_main_menu(user_id)
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ پست با موفقیت به {channel} ارسال شد.\n🏠 منوی اصلی:", reply_markup=get_main_menu(user_id))
                data_store.last_message_id[user_id] = msg.message_id
            data_store.reset_user_state(user_id)
        return

    if state == "post_with_signature_ready":
        if text == "🆕 پست جدید":
            data_store.reset_user_state(user_id)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for sig_name in data_store.signatures.keys():
                markup.add(types.KeyboardButton(sig_name))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            data_store.update_user_state(user_id, "select_signature")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🖊️ امضای مورد نظر را انتخاب کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ امضای مورد نظر را انتخاب کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        elif text == "⏰ زمان‌بندی پست":
            if not data_store.channels:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ هیچ چنلی ثبت نشده است. ابتدا یک چنل ثبت کنید.",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ چنلی ثبت نشده است. ابتدا یک چنل ثبت کنید.", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            else:
                channels_list = "\n".join(data_store.channels)
                one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
                data_store.update_user_state(user_id, "schedule_post")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n📢 چنل‌های ثبت‌شده:\n{channels_list}\n\n⏰ زمان پیشنهادی: <code>{one_minute_later}</code>\nلطفاً چنل و زمان آینده را وارد کنید (مثال: <code>@channel {one_minute_later}</code>):",
                        reply_markup=get_back_menu(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n📢 چنل‌های ثبت‌شده:\n{channels_list}\n\n⏰ زمان پیشنهادی: <code>{one_minute_later}</code>\nلطفاً چنل و زمان آینده را وارد کنید (مثال: <code>@channel {one_minute_later}</code>):", reply_markup=get_back_menu(), parse_mode="HTML")
                    data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state == "schedule_post":
        try:
            parts = text.split()
            if len(parts) < 3:
                tehran_tz = pytz.timezone('Asia/Tehran')
                one_minute_later = (datetime.now(tehran_tz) + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ لطفاً چنل و زمان آینده را وارد کنید (مثال: <code>@channel {one_minute_later}</code>)",
                        reply_markup=get_back_menu(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لطفاً چنل و زمان آینده را وارد کنید (مثال: <code>@channel {one_minute_later}</code>)", reply_markup=get_back_menu(), parse_mode="HTML")
                    data_store.last_message_id[user_id] = msg.message_id
                return
            
            channel = parts[0]
            time_str = " ".join(parts[1:])
            scheduled_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
            
            if scheduled_time <= datetime.now():
                one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ فقط زمان آینده قابل قبول است! زمان پیشنهادی: <code>{one_minute_later}</code>",
                        reply_markup=get_back_menu(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ فقط زمان آینده قابل قبول است! زمان پیشنهادی: <code>{one_minute_later}</code>", reply_markup=get_back_menu(), parse_mode="HTML")
                    data_store.last_message_id[user_id] = msg.message_id
                return
            
            if channel not in data_store.channels:
                one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ این چنل ثبت نشده است. ابتدا چنل را ثبت کنید. زمان پیشنهادی: <code>{one_minute_later}</code>",
                        reply_markup=get_back_menu(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این چنل ثبت نشده است. ابتدا چنل را ثبت کنید. زمان پیشنهادی: <code>{one_minute_later}</code>", reply_markup=get_back_menu(), parse_mode="HTML")
                    data_store.last_message_id[user_id] = msg.message_id
                return
            
            post_content = user_state["data"].get("post_content", "")
            media_paths = user_state["data"].get("media_paths", [])
            inline_buttons = user_state["data"].get("inline_buttons", [])
            row_width = user_state["data"].get("row_width", 4)
            
            job_id = str(uuid.uuid4())
            data_store.scheduled_posts.append({
                "job_id": job_id,
                "channel": channel,
                "time": time_str,
                "post_content": post_content,
                "media_paths": media_paths if media_paths else [],
                "inline_buttons": inline_buttons,
                "row_width": row_width
            })
            data_store.save_data()
            
            schedule.every().day.at(scheduled_time.strftime("%H:%M")).do(send_scheduled_post, job_id=job_id).tag(job_id)
            markup = get_main_menu(user_id)
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ پست برای ارسال به {channel} در زمان {time_str} زمان‌بندی شد.\n منوی اصلی:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ پست برای ارسال به {channel} در زمان {time_str} زمان‌بندی شد.\n منوی اصلی:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
            data_store.reset_user_state(user_id)
        except ValueError:
            one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ فرمت زمان اشتباه است! از yyyy/mm/dd hh:mm استفاده کنید. زمان پیشنهادی: <code>{one_minute_later}</code>",
                    reply_markup=get_back_menu(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ فرمت زمان اشتباه است! از yyyy/mm/dd hh:mm استفاده کنید. زمان پیشنهادی: <code>{one_minute_later}</code>", reply_markup=get_back_menu(), parse_mode="HTML")
                data_store.last_message_id[user_id] = msg.message_id
        except Exception as e:
            logger.error(f"خطا در تنظیم تایمر: {e}")
            one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ یه مشکلی پیش اومد. دوباره امتحان کنید. زمان پیشنهادی: <code>{one_minute_later}</code>",
                    reply_markup=get_back_menu(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ یه مشکلی پیش اومد. دوباره امتحان کنید. زمان پیشنهادی: <code>{one_minute_later}</code>", reply_markup=get_back_menu(), parse_mode="HTML")
                data_store.last_message_id[user_id] = msg.message_id
        return  
  
    if state == "new_signature_name":
        if text in data_store.signatures:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ این نام امضا قبلاً وجود دارد.\n✏️ نام دیگری وارد کنید:",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این نام امضا قبلاً وجود دارد.\n✏️ نام دیگری وارد کنید:", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            data_store.update_user_state(user_id, "new_signature_template", {"new_sig_name": text})
            example = "[5253877736207821121] {name}\n[5256160369591723706] {description}\n[5253864872780769235] {version}"
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🖊️ قالب امضا را وارد کنید.\nمثال:\n{example}",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ قالب امضا را وارد کنید.\nمثال:\n{example}", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state == "new_signature_template":
        template = text
        sig_name = user_state["data"]["new_sig_name"]
        variables = re.findall(r'\{(\w+)\}', template)
        
        if not variables:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ حداقل یک متغیر با فرمت {{variable_name}} وارد کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ حداقل یک متغیر با فرمت {{variable_name}} وارد کنید.", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        
        undefined_vars = [var for var in variables if var not in data_store.controls]
        if undefined_vars:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ متغیرهای زیر تعریف نشده‌اند: {', '.join(undefined_vars)}\nلطفاً ابتدا این متغیرها را در بخش 'مدیریت متغیرها' تعریف کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ متغیرهای زیر تعریف نشده‌اند: {', '.join(undefined_vars)}\nلطفاً ابتدا این متغیرها را در بخش 'مدیریت متغیرها' تعریف کنید.", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        
        data_store.signatures[sig_name] = {
            "template": template,
            "variables": variables
        }
        data_store.save_data()
        
        markup = get_main_menu(user_id)
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n✅ امضای جدید '{sig_name}' ایجاد شد.\n🏠 منوی اصلی:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✅ امضای جدید '{sig_name}' ایجاد شد.\n🏠 منوی اصلی:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
        
        data_store.reset_user_state(user_id)
        return
    
    if state == "delete_signature":
        if text in data_store.signatures:
            del data_store.signatures[text]
            data_store.save_data()
            markup = get_signature_management_menu()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ امضای '{text}' حذف شد.\n✍️ مدیریت امضاها:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ امضای '{text}' حذف شد.\n✍️ مدیریت امضاها:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "signature_management")
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ امضای انتخاب‌شده وجود ندارد.",
                    reply_markup=get_signature_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ امضای انتخاب‌شده وجود ندارد.", reply_markup=get_signature_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state == "admin_management":
        status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n⛔️ قابلیت مدیریت ادمین‌ها حذف شده است.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ قابلیت مدیریت ادمین‌ها حذف شده است.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
        return
    
    if state in ["variable_management", "select_variable_format", "add_variable", "remove_variable"]:
        handle_variable_management(user_id, text)
        return
    
    if state == "set_default_settings":
        data_store.settings["default_welcome"] = text
        data_store.save_data()
        markup = get_main_menu(user_id)
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n✅ متن پیش‌فرض تنظیم شد.\n🏠 منوی اصلی:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✅ متن پیش‌فرض تنظیم شد.\n🏠 منوی اصلی:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
        data_store.reset_user_state(user_id)
        return
    
    if state == "register_channel":
        channel_name = text.strip()
        if not channel_name.startswith('@'):
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ آیدی چنل باید با @ شروع شود (مثال: @channelname).",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ آیدی چنل باید با @ شروع شود (مثال: @channelname).", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        required_permissions = [
            ("ارسال پیام", False),
            ("مدیریت پیام‌ها", False)
        ]
        try:
            chat = bot.get_chat(channel_name)
            bot_member = bot.get_chat_member(channel_name, bot.get_me().id)
            
            # بررسی نوع عضویت
            if bot_member.status not in ['administrator', 'creator']:
                required_permissions = [
                    ("ارسال پیام", False),
                    ("ویرایش پیام‌های دیگران", False),
                    ("حذف پیام‌های دیگران", False),
                    ("ادمین کردن کاربران", False)
                ]
            else:
                # بررسی دسترسی‌های واقعی برای ادمین
                can_post = bot_member.can_post_messages if hasattr(bot_member, 'can_post_messages') else True
                can_edit = bot_member.can_edit_messages if hasattr(bot_member, 'can_edit_messages') else False
                can_delete = bot_member.can_delete_messages if hasattr(bot_member, 'can_delete_messages') else False
                can_promote = bot_member.can_promote_members if hasattr(bot_member, 'can_promote_members') else False
                
                required_permissions = [
                    ("ارسال پیام", can_post),
                    ("ویرایش پیام‌های دیگران", can_edit),
                    ("حذف پیام‌های دیگران", can_delete),
                    ("ادمین کردن کاربران", can_promote)
                ]
            
            if not all(granted for _, granted in required_permissions):
                permissions_text = "\n".join(
                    f"{name}: {'✅' if granted else '❌'}" for name, granted in required_permissions
                )
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ هیچ قابلیتی بهم ندادی!\n{permissions_text}\nلطفاً دسترسی‌های لازم را بدهید.",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ قابلیتی بهم ندادی!\n{permissions_text}\nلطفاً دسترسی‌های لازم را بدهید.", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                return
            if channel_name in data_store.channels:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ این چنل قبلاً ثبت شده است.",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این چنل قبلاً ثبت شده است.", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                return
            data_store.channels.append(channel_name)
            data_store.save_data()
            permissions_text = "\n".join(
                f"{name}: ✅" for name, _ in required_permissions
            )
            markup = get_main_menu(user_id)
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n{permissions_text}\n✅ چنل {channel_name} چک شد و به حافظه اضافه شد.\n🏠 منوی اصلی:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n{permissions_text}\n✅ چنل {channel_name} چک شد و به حافظه اضافه شد.\n🏠 منوی اصلی:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
            data_store.reset_user_state(user_id)
            return
        except Exception as e:
            logger.error(f"خطا در بررسی دسترسی چنل {channel_name}: {e}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ خطا در بررسی چنل {channel_name}. لطفاً مطمئن شوید که ربات به چنل دسترسی دارد و دوباره امتحان کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در بررسی چنل {channel_name}. لطفاً مطمئن شوید که ربات به چنل دسترسی دارد و دوباره امتحان کنید.", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return

    if state == "broadcast_timer_or_instant":
        if text == "⏰ ارسال تایمردار":
            data_store.update_user_state(user_id, "broadcast_wait_for_timer", user_state["data"])
            bot.send_message(user_id, "⏰ برای تایمر زمان را وارد کنید :\nاین زمان باید متعلق به آینده باشد.\nباید در قالب yyyy/mm/dd hh:mm باشد.\nبه عنوان مثال زمان حال در ۵ دقیقه بعد:\n<code>{example}</code>", reply_markup=get_back_menu())
            return
        if text == "🚀 ارسال فوری":
            broadcast_mode = user_state["data"].get("broadcast_mode")
            broadcast_msg = user_state["data"].get("broadcast_message")
            send_broadcast_instant(user_id, broadcast_msg, broadcast_mode)
            # پیام موفقیت بعد از ارسال واقعی (در send_broadcast_instant انجام می‌شود)
            data_store.reset_user_state(user_id)
            return
        bot.send_message(user_id, "لطفاً یکی از گزینه‌های ارسال را انتخاب کنید:", reply_markup=get_back_menu())
        return

# ارسال پست زمان‌بندی‌شده
def send_scheduled_post(job_id):
    if not data_store.timer_settings.get("timers_enabled", True):
        logger.info(f"تایمر {job_id} اجرا نشد چون تایمرها غیرفعال هستند.")
        return
    for post in data_store.scheduled_posts:
        if post["job_id"] == job_id:
            channel = post["channel"]
            post_content = post["post_content"]
            media_paths = post["media_paths"]
            inline_buttons = post["inline_buttons"]
            row_width = post.get("row_width", 4)
            
            inline_keyboard = None
            if data_store.timer_settings.get("inline_buttons_enabled", True) and inline_buttons:
                inline_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
                for button in inline_buttons:
                    inline_keyboard.add(types.InlineKeyboardButton(button["text"], url=button["url"]))
            
            try:
                stats_path = os.path.join("helper", "stats.json")
                if os.path.exists(stats_path):
                    with open(stats_path, 'r', encoding='utf-8') as f:
                        stats = json.load(f)
                else:
                    stats = {"files": []}
                
                if media_paths:
                    for media in media_paths:
                        media_path = os.path.join("medias", os.path.basename(media["path"]))
                        if not os.path.exists(media_path):
                            logger.error(f"فایل رسانه {media_path} یافت نشد.")
                            continue
                        with open(media_path, "rb") as file:
                            if media["type"] == "photo":
                                bot.send_photo(channel, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                            elif media["type"] == "video":
                                bot.send_video(channel, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                        # به‌روزرسانی وضعیت فایل در stats.json
                        for file_detail in stats["files"]:
                            if file_detail["path"] == media_path:
                                file_detail["status"] = "sent"
                else:
                    bot.send_message(channel, post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                
                # ذخیره تغییرات در stats.json
                with open(stats_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, ensure_ascii=False, indent=4)
                
                data_store.scheduled_posts.remove(post)
                data_store.save_data()
                schedule.clear(job_id)
            except Exception as e:
                logger.error(f"خطا در ارسال پست زمان‌بندی‌شده {job_id}: {e}")
            break

# پردازش دکمه‌های منو
def process_main_menu_button(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")

    if text == "🔙 بازگشت به منوی اصلی":
        data_store.reset_user_state(user_id)
        markup = get_main_menu(user_id)
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🏠 بازگشت به منوی اصلی:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True

    elif text == "🛡️ امکانات اجباری":
        data_store.update_user_state(user_id, "mandatory_features_menu")
        msg = bot.send_message(user_id, "🔒 امکانات اجباری:", reply_markup=get_mandatory_features_menu())
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "📢 چنل اجباری":
        data_store.update_user_state(user_id, "mandatory_channel_menu")
        msg = bot.send_message(user_id, "📢 مدیریت چنل‌های اجباری:", reply_markup=get_mandatory_channel_menu())
        data_store.last_message_id[user_id] = msg.message_id
        # لیست چنل‌های ثبت‌شده را هم نمایش بده
        chlist = "\n".join(data_store.mandatory_channels) or "هیچ چنلی ثبت نشده."
        bot.send_message(user_id, f"لیست چنل‌های اجباری:\n{chlist}")
        return True
    elif text == "👁️ سین اجباری":
        data_store.update_user_state(user_id, "mandatory_seen_menu")
        msg = bot.send_message(user_id, "👁️ مدیریت سین اجباری:", reply_markup=get_mandatory_seen_menu())
        data_store.last_message_id[user_id] = msg.message_id
        chlist = "\n".join(data_store.mandatory_seen_channels) or "هیچ چنلی ثبت نشده."
        bot.send_message(user_id, f"لیست چنل‌های سین اجباری:\n{chlist}\nتعداد پست سین: {data_store.mandatory_seen_count}")
        return True
    elif text == "💬 ری اکشن اجباری":
        data_store.update_user_state(user_id, "mandatory_reaction_menu")
        msg = bot.send_message(user_id, "💬 مدیریت ری اکشن اجباری:", reply_markup=get_mandatory_reaction_menu())
        data_store.last_message_id[user_id] = msg.message_id
        chlist = "\n".join(data_store.mandatory_reaction_channels) or "هیچ چنلی ثبت نشده."
        bot.send_message(user_id, f"لیست چنل‌های ری اکشن اجباری:\n{chlist}")
        return True
    elif text == "📣 ارسال همگانی":
        # فقط برای اونر یا ادمین با دسترسی
        if not (is_owner(user_id) or (user_id in data_store.admins and data_store.admin_permissions.get(str(user_id), {}).get("broadcast_management", False))):
            msg = bot.send_message(
                user_id,
                "⛔️ دسترسی به ارسال همگانی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton("🗨️ ارسال با نقل قول"), types.KeyboardButton("✉️ ارسال بدون نقل قول"))
        markup.add(types.KeyboardButton("📢 ثبت چنل اپلودری"))  # دکمه جدید
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "broadcast_choose_mode", {})
        msg = bot.send_message(
            user_id,
            "لطفاً روش ارسال همگانی را انتخاب کنید:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "📤 اپلودر":
        data_store.update_user_state(user_id, "uploader_menu", {})
        status_text = data_store.state_messages.get("uploader_menu", "در حال حاضر در منوی اپلودر هستید.")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n📤 اپلودر:\nیکی از گزینه‌های زیر را انتخاب کنید.",
            reply_markup=get_uploader_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "✨ مدیریت اپشن‌ها":
        data_store.update_user_state(user_id, "timer_inline_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n✨ مدیریت اپشن‌ها:",
            reply_markup=get_timer_inline_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "👤 مدیریت ادمین‌ها":
        if not is_owner(user_id):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ فقط اونر به این بخش دسترسی دارد.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        data_store.update_user_state(user_id, "admin_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n👤 مدیریت ادمین‌ها:",
            reply_markup=get_admin_management_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "🆕 ایجاد پست":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for sig_name in data_store.signatures.keys():
            markup.add(types.KeyboardButton(sig_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "select_signature")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🖊️ امضای مورد نظر را انتخاب کنید:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "📝 مدیریت مقادیر پیش‌فرض":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = get_default_values_management_menu()
        data_store.update_user_state(user_id, "default_values_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n📝 مدیریت مقادیر پیش‌فرض:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "✍️ مدیریت امضاها":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = get_signature_management_menu()
        data_store.update_user_state(user_id, "signature_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n✍️ مدیریت امضاها:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "⚙️ مدیریت متغیرها":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = get_variable_management_menu()
        data_store.update_user_state(user_id, "variable_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n⚙️ مدیریت متغیرها:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "🏠 تنظیمات پیش‌فرض":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        data_store.update_user_state(user_id, "set_default_settings")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🖊️ متن پیش‌فرض خوش‌آمدگویی را وارد کنید:",
            reply_markup=get_back_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "📢 ثبت چنل":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        data_store.update_user_state(user_id, "register_channel")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🖊️ آیدی چنل را وارد کنید (مثال: @channelname):",
            reply_markup=get_back_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "⏰ مدیریت تایمرها":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        if not data_store.scheduled_posts:
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n📅 هیچ تایمری تنظیم نشده است.\n🏠 منوی اصلی:",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        timers_text = f"{status_text}\n\n⏰ تایمرهای تنظیم‌شده:\n\n"
        try:
            stats_path = os.path.join("helper", "stats.json")
            if os.path.exists(stats_path):
                with open(stats_path, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {"files": []}
            for post in data_store.scheduled_posts:
                timers_text += f"🆔 {post['job_id']}\nچنل: {post['channel']}\nزمان: {post['time']}\n"
                if post.get("media_paths"):
                    for media in post["media_paths"]:
                        for file_detail in stats["files"]:
                            if file_detail["path"] == os.path.join("medias", os.path.basename(media["path"])):
                                status = file_detail.get("status", "pending")
                                timers_text += (
                                    f"📄 فایل: {file_detail['name']}\n"
                                    f"نوع: {file_detail['type']}\n"
                                    f"حجم: {file_detail['size_mb']:.2f} MB\n"
                                    f"وضعیت: {'ارسال شده' if status == 'sent' else 'در انتظار'}\n"
                                )
                timers_text += "\n"
            inline_keyboard = types.InlineKeyboardMarkup()
            for post in data_store.scheduled_posts:
                inline_keyboard.add(types.InlineKeyboardButton(f"حذف تایمر {post['job_id']}", callback_data=f"delete_timer_{post['job_id']}"))
            msg = bot.send_message(
                user_id,
                timers_text,
                reply_markup=inline_keyboard
            )
            data_store.last_message_id[user_id] = msg.message_id
        except Exception as e:
            logger.error(f"خطا در نمایش تایمرها: {e}")
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⚠️ خطا در بارگذاری اطلاعات تایمرها.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
        return True

    elif text == f"🤖 بات دستیار نسخه {BOT_VERSION}":
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🤖 این بات دستیار نسخه {BOT_VERSION} است.\nتوسعه توسط @py_zon",
            reply_markup=get_main_menu(user_id)
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "🔧 تنظیم دسترسی ادمین‌ها":
        if not is_owner(user_id):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ فقط اونر به این بخش دسترسی دارد.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        if not data_store.admins:
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⚠️ هیچ ادمینی وجود ندارد.",
                reply_markup=get_admin_management_menu()
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for admin_id in data_store.admins:
            markup.add(types.KeyboardButton(str(admin_id)))
        markup.add(types.KeyboardButton("🔙 بازگشت به مدیریت ادمین"))
        data_store.update_user_state(user_id, "select_admin_for_permissions")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🔧 آیدی ادمینی که می‌خواهید دسترسی‌هایش را تنظیم کنید را انتخاب کنید:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    return False
# مدیریت امضاها
def handle_signature_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")

    if text == "👀 مشاهده امضاها":
        signatures_text = f"{status_text}\n\n📋 لیست امضاها:\n\n"
        if not data_store.signatures:
            signatures_text += "هیچ امضایی وجود ندارد.\n"
        else:
            for sig_name, sig_data in data_store.signatures.items():
                template = sig_data["template"]
                variables = sig_data["variables"]
                preview_content = template
                for var in variables:
                    var_format = data_store.controls.get(var, {}).get("format", "Simple")
                    if var_format == "Bold":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<b>[{var}]</b>")
                    elif var_format == "Italic":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<i>[{var}]</i>")
                    elif var_format == "Code":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<code>[{var}]</code>")
                    elif var_format == "Strike":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<s>[{var}]</s>")
                    elif var_format == "Underline":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<u>[{var}]</u>")
                    elif var_format == "Spoiler":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<tg-spoiler>[{var}]</tg-spoiler>")
                    elif var_format == "BlockQuote":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<blockquote>[{var}]</blockquote>")
                    else:
                        preview_content = preview_content.replace(f"{{{var}}}", f"[{var}]")
                signatures_text += f"🔹 امضا: {sig_name}\n📝 متن:\n{preview_content}\n\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=signatures_text,
                reply_markup=get_signature_management_menu(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, signatures_text, reply_markup=get_signature_management_menu(), parse_mode="HTML")
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➕ افزودن امضای جدید":
        data_store.update_user_state(user_id, "new_signature_name")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n✏️ نام امضای جدید را وارد کنید:",
                reply_markup=get_back_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✏️ نام امزای جدید را وارد کنید:", reply_markup=get_back_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "🗑️ حذف امضا":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for sig_name in data_store.signatures.keys():
            markup.add(types.KeyboardButton(sig_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "delete_signature")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n🗑️ امضای مورد نظر برای حذف را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ امزای مورد نظر برای حذف را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id

def get_mandatory_features_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("📢 چنل اجباری"), types.KeyboardButton("👁️ سین اجباری"))
    markup.add(types.KeyboardButton("💬 ری اکشن اجباری"))
    markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    return markup

def get_mandatory_channel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("➕ افزودن چنل اجباری"))
    markup.add(types.KeyboardButton("➖ حذف چنل اجباری"))
    markup.add(types.KeyboardButton("📝 ثبت پیام جوین اجباری"))
    markup.add(types.KeyboardButton("🔙 بازگشت به امکانات اجباری"))
    return markup

def get_mandatory_seen_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("➕ افزودن چنل سین اجباری"))
    markup.add(types.KeyboardButton("➖ حذف چنل سین اجباری"))
    markup.add(types.KeyboardButton("📝 ثبت پیام سین اجباری"))
    markup.add(types.KeyboardButton("🔢 تعداد پست سین"))
    markup.add(types.KeyboardButton("🔙 بازگشت به امکانات اجباری"))
    return markup

def get_mandatory_reaction_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("➕ افزودن چنل ری اکشن اجباری"))
    markup.add(types.KeyboardButton("➖ حذف چنل ری اکشن اجباری"))
    markup.add(types.KeyboardButton("📝 ثبت پیام ری اکشن اجباری"))
    markup.add(types.KeyboardButton("🔙 بازگشت به امکانات اجباری"))
    return markup

# مدیریت کنترل‌ها
def get_variable_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    view_btn = types.KeyboardButton("👀 مشاهده متغیرها")
    add_btn = types.KeyboardButton("➕ افزودن متغیر")
    remove_btn = types.KeyboardButton("➖ حذف متغیر")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(view_btn, add_btn)
    markup.add(remove_btn, back_btn)
    return markup

def get_text_format_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    formats = [
        "Bold", "Italic", "Code", "Strike",
        "Underline", "Spoiler", "BlockQuote", "Simple", "Link"
    ]
    for fmt in formats:
        markup.add(types.KeyboardButton(fmt))
    markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    return markup

def handle_variable_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    if text == "👀 مشاهده متغیرها":
        variables_text = f"{status_text}\n\n⚙️ متغیرها:\n\n"
        if not data_store.controls:
            variables_text += "هیچ متغیری وجود ندارد.\n"
        else:
            for var_name, var_data in data_store.controls.items():
                variables_text += f"🔹 {var_name}: نوع {var_data['format']}\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=variables_text,
                reply_markup=get_variable_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, variables_text, reply_markup=get_variable_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➕ افزودن متغیر":
        data_store.update_user_state(user_id, "select_variable_format")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n🖊️ نوع متغیر را انتخاب کنید:",
                reply_markup=get_text_format_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ نوع متغیر را انتخاب کنید:", reply_markup=get_text_format_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➖ حذف متغیر":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for var_name in data_store.controls.keys():
            markup.add(types.KeyboardButton(var_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "remove_variable")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n🗑️ متغیری که می‌خواهید حذف کنید را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ متغیری که می‌خواهید حذف کنید را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
            
    elif state == "select_variable_format":
        if text in ["Bold", "Italic", "Code", "Strike", "Underline", "Spoiler", "BlockQuote", "Simple"]:
            data_store.update_user_state(user_id, "add_variable", {"selected_format": text})
            try:
                bot.send_message(
                    user_id,
                    f"{status_text}\n\n🖊️ نام متغیر جدید را وارد کنید (به انگلیسی، بدون فاصله):",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ارسال پیام درخواست نام متغیر: {e}")
            return
        else:
            try:
                bot.send_message(
                    user_id,
                    f"{status_text}\n\n⚠️ نوع نامعتبر! لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
                    reply_markup=get_text_format_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ارسال پیام نوع نامعتبر: {e}")
            return
        
    elif user_state["state"] == "add_variable":
        if not re.match(r'^[a-zA-Z0-9_]+$', text):
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ نام متغیر باید به انگلیسی و بدون فاصله باشد!",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ نام متغیر باید به انگلیسی و بدون فاصله باشد!", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        if text in data_store.controls:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ این نام متغیر قبلاً وجود دارد!",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این نام متغیر قبلاً وجود دارد!", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        data_store.controls[text] = {"format": user_state["data"]["selected_format"]}
        data_store.save_data()
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n✅ متغیر '{text}' با نوع {user_state['data']['selected_format']} اضافه شد.\n⚙️ مدیریت متغیرها:",
                reply_markup=get_variable_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✅ متغیر '{text}' با نوع {user_state['data']['selected_format']} اضافه شد.\n⚙️ مدیریت متغیرها:", reply_markup=get_variable_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "variable_management")
    
    elif user_state["state"] == "remove_variable":
        if text in data_store.controls:
            del data_store.controls[text]
            data_store.save_data()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ متغیر '{text}' حذف شد.\n⚙️ مدیریت متغیرها:",
                    reply_markup=get_variable_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ متغیر '{text}' حذف شد.\n⚙️ مدیریت متغیرها:", reply_markup=get_variable_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ متغیر انتخاب‌شده وجود ندارد.",
                    reply_markup=get_variable_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ متغیر انتخاب‌شده وجود ندارد.", reply_markup=get_variable_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "variable_management")

    elif user_state["state"] == "remove_variable":
        if text in data_store.controls:
            # چک کن که متغیر توی هیچ امضایی استفاده نشده باشه
            used_in_signatures = []
            for sig_name, sig_data in data_store.signatures.items():
                if text in sig_data["variables"]:
                    used_in_signatures.append(sig_name)
            if used_in_signatures:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ متغیر '{text}' در امضاهای {', '.join(used_in_signatures)} استفاده شده است. ابتدا این امضاها را ویرایش یا حذف کنید.",
                        reply_markup=get_variable_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ متغیر '{text}' در امضاهای {', '.join(used_in_signatures)} استفاده شده است. ابتدا این امضاها را ویرایش یا حذف کنید.", reply_markup=get_variable_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                return
            del data_store.controls[text]
            data_store.save_data()

def get_default_values_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    view_btn = types.KeyboardButton("👀 مشاهده مقادیر پیش‌فرض")
    set_btn = types.KeyboardButton("➕ تنظیم مقدار پیش‌فرض")
    remove_btn = types.KeyboardButton("➖ حذف مقدار پیش‌فرض")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(view_btn, set_btn)
    markup.add(remove_btn, back_btn)
    return markup

def handle_default_values_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state.get("state", None)  # بهینه‌سازی: بررسی وجود state
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    if not (is_owner(user_id) or is_admin(user_id)):
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای عدم دسترسی: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n⛔️ دسترسی ندارید.", reply_markup=get_main_menu(user_id))
            data_store.last_message_id[user_id] = msg.message_id
        return
    
    if text == "👀 مشاهده مقادیر پیش‌فرض":
        values_text = f"{status_text}\n\n📝 مقادیر پیش‌فرض:\n\n"
        if not data_store.default_values:
            values_text += "هیچ مقدار پیش‌فرضی وجود ندارد.\n"
        else:
            for var_name, value in data_store.default_values.items():
                values_text += f"🔹 {var_name}: {value}\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=values_text,
                reply_markup=get_default_values_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای مشاهده مقادیر: {e}")
            msg = bot.send_message(user_id, values_text, reply_markup=get_default_values_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➕ تنظیم مقدار پیش‌فرض":
        if not data_store.controls:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ هیچ متغیری تعریف نشده است.",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای عدم وجود متغیر: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ متغیری تعریف نشده است.", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for var_name in data_store.controls.keys():
            markup.add(types.KeyboardButton(var_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "set_default_value_select_var")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n🖊️ متغیری که می‌خواهید مقدار پیش‌فرض برای آن تنظیم کنید را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای تنظیم مقدار: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ متغیری که می‌خواهید مقدار پیش‌فرض برای آن تنظیم کنید را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➖ حذف مقدار پیش‌فرض":
        if not data_store.default_values:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ هیچ مقدار پیش‌فرضی برای حذف وجود ندارد.",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای عدم وجود مقدار پیش‌فرض: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ مقدار پیش‌فرضی برای حذف وجود ندارد.", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for var_name in data_store.default_values.keys():
            markup.add(types.KeyboardButton(var_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "remove_default_value")
        try:
            bot.edit_message_text(
                chat_id=user_id,  # اصلاح خطا: chatelder به chat_id تغییر کرد
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n🗑️ متغیری که می‌خواهید مقدار پیش‌فرض آن را حذف کنید را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای حذف مقدار پیش‌فرض: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ متغیری که می‌خواهید مقدار پیش‌فرض آن را حذف کنید را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id

    elif state == "set_default_value_select_var":
        if text in data_store.controls:
            data_store.update_user_state(user_id, "set_default_value", {"selected_var": text})
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n🖊️ مقدار پیش‌فرض برای '{text}' را وارد کنید:",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای وارد کردن مقدار پیش‌فرض: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ مقدار پیش‌فرض برای '{text}' را وارد کنید:", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ متغیر انتخاب‌شده وجود ندارد.",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای متغیر ناموجود: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ متغیر انتخاب‌شده وجود ندارد.", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "default_values_management")

    elif state == "set_default_value":
        prev = data_store.default_values.get(user_state["data"]["selected_var"])
        data_store.default_values[user_state["data"]["selected_var"]] = text
        data_store.save_data()
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n✅ مقدار پیش‌فرض برای '{user_state['data']['selected_var']}' تنظیم شد (قبلی: {prev if prev else 'نداشت'}).\n📝 مدیریت مقادیر پیش‌فرض:",
                reply_markup=get_default_values_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای تنظیم موفق: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✅ مقدار پیش‌فرض برای '{user_state['data']['selected_var']}' تنظیم شد (قبلی: {prev if prev else 'نداشت'}).\n📝 مدیریت مقادیر پیش‌فرض:", reply_markup=get_default_values_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "default_values_management")
    
    elif state == "remove_default_value":
        if text in data_store.default_values:
            del data_store.default_values[text]
            data_store.save_data()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n✅ مقدار پیش‌فرض برای '{text}' حذف شد.\n📝 مدیریت مقادیر پیش‌فرض:",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای حذف موفق: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ مقدار پیش‌فرض برای '{text}' حذف شد.\n📝 مدیریت مقادیر پیش‌فرض:", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ مقدار پیش‌فرض برای '{text}' وجود ندارد.",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای مقدار پیش‌فرض ناموجود: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ مقدار پیش‌فرض برای '{text}' وجود ندارد.", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "default_values_management")

# هندلر دکمه‌های شیشه‌ای برای حذف تایمرها
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_timer_"))
def delete_timer_callback(call):
    user_id = call.from_user.id
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    job_id = call.data.replace("delete_timer_", "")
    for post in data_store.scheduled_posts:
        if post["job_id"] == job_id:
            data_store.scheduled_posts.remove(post)
            data_store.save_data()
            schedule.clear(job_id)
            break
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=data_store.last_message_id[user_id],
            text=f"{status_text}\n\n✅ تایمر {job_id} حذف شد.\n🏠 منوی اصلی:",
            reply_markup=get_main_menu(user_id)
        )
    except Exception as e:
        logger.error(f"خطا در ویرایش پیام: {e}")
        msg = bot.send_message(user_id, f"{status_text}\n\n✅ تایمر {job_id} حذف شد.\n🏠 منوی اصلی:", reply_markup=get_main_menu(user_id))
        data_store.last_message_id[user_id] = msg.message_id

@bot.message_handler(commands=["start"])
def start_with_file(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("https://t.me/"):
        file_link = args[1]
        file_info = data_store.uploader_file_map.get(file_link)
        if not file_info:
            bot.send_message(user_id, "⚠️ فایل مورد نظر یافت نشد یا حذف شده است.")
            return
        channel_username = file_link.split('/')[3]
        msg_id = int(file_link.split('/')[4])
        try:
            bot.forward_message(chat_id=user_id, from_chat_id=f"@{channel_username}", message_id=msg_id)
        except Exception as e:
            bot.send_message(user_id, "⚠️ خطا در ارسال فایل.")
        return
    # حالت عادی استارت بقیه کد قبلی start_command
    start_command(message)

# بعد از تعریف توابع و کلاس‌ها
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    data_store.last_user_message_id[user_id] = message.message_id
    
    if text in MAIN_MENU_BUTTONS:
        if process_main_menu_button(user_id, text):
            return
    
    elif state == "admin_management":
        handle_admin_management(user_id, text)
    elif state == "signature_management":
        handle_signature_management(user_id, text)
    elif state == "variable_management":
        handle_variable_management(user_id, text)
    elif state == "default_values_management":
        handle_default_values_management(user_id, text)
    # اضافه کردن یک else برای مدیریت حالتی که هیچ شرطی مطابقت ندارد
    else:
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n⚠️ دستور نامعتبر. لطفاً از منو گزینه‌ای انتخاب کنید.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⚠️ دستور نامعتبر. لطفاً از منو گزینه‌ای انتخاب کنید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            
def super_stable_connection_monitor(bot: telebot.TeleBot, check_interval: int = 5):
    """
    مانیتورینگ بسیار پایدار polling با auto-recover و اطلاع‌رسانی به OWNER.
    اگر حتی یک لحظه ارتباط قطع شود یا polling کرش کند، خودش بی‌وقفه ری‌استارت می‌شود.
    """
    def is_telegram_alive():
        try:
            resp = requests.get(f"https://api.telegram.org/bot{bot.token}/getMe", timeout=20)
            ok = resp.status_code == 200 and resp.json().get("ok", False)
            if not ok:
                logger.warning(f"[CHECK] getMe failed: {resp.status_code} {resp.text}")
            return ok
        except Exception as e:
            logger.warning(f"[CHECK] getMe Exception: {e}")
            return False

    def polling_forever():
        """این ترد تا ابد polling را اجرا می‌کند، اگر کرش کند خودش ری‌استارت می‌شود."""
        while True:
            try:
                logger.info("⏳ [POLLING] شروع polling ...")
                bot.polling(non_stop=True, interval=3, timeout=20, long_polling_timeout=30)
            except Exception as e:
                logger.error(f"❌ [POLLING] Exception: {e}\n{traceback.format_exc()}")
                time.sleep(5)

    # فقط یکبار این ترد را اجرا کن!
    polling_thread = threading.Thread(target=polling_forever, daemon=True)
    polling_thread.start()

    # مانیتورینگ: اگر ارتباط واقعا قطع شد/ترد polling مرد، اطلاع بده و ری‌استارت کن
    def monitor():
        nonlocal polling_thread
        last_status = True
        notified_down = False
        while True:
            alive = polling_thread.is_alive() and is_telegram_alive()
            if alive:
                if not last_status:
                    # تازه وصل شده
                    logger.info("✅ [MONITOR] ارتباط دوباره برقرار شد.")
                    try:
                        bot.send_message(OWNER_ID, f"✅ ربات دوباره آنلاین شد! نسخه {BOT_VERSION}")
                    except: pass
                last_status = True
                notified_down = False
            else:
                logger.warning("❌ [MONITOR] ارتباط/ترد polling قطع است. تلاش برای ری‌استارت ...")
                if not notified_down:
                    try:
                        bot.send_message(OWNER_ID, f"❌ ربات آفلاین شد! تلاش برای ری‌استارت... نسخه {BOT_VERSION}")
                    except: pass
                    notified_down = True
                # ری‌استارت ترد polling اگر مرده
                if not polling_thread.is_alive():
                    try:
                        polling_thread2 = threading.Thread(target=polling_forever, daemon=True)
                        polling_thread2.start()
                        polling_thread = polling_thread2
                        logger.info("[MONITOR] ترد جدید polling استارت شد.")
                    except Exception as e:
                        logger.error(f"❌ [MONITOR] ری‌استارت ترد polling: {e}")
                last_status = False
            # اجرای زمان‌بندی schedule if needed
            try:
                schedule.run_pending()
            except Exception as e:
                logger.error(f"❌ [MONITOR] خطا در schedule: {e}")
            time.sleep(check_interval)

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    logger.info(f"[MONITOR] ترد مانیتورینگ و polling با فاصله {check_interval} ثانیه استارت شد.")

# ---- MAIN ----
def update_uploader_stats():
    uploader_files_total = 0
    uploader_files_total_size = 0
    for file_info in data_store.uploader_file_map.values():
        ch_link = file_info.get("channel_link")
        if ch_link:
            uploader_files_total += 1
            msg_id = int(ch_link.split("/")[-1])
            for ext in ['jpg', 'jpeg', 'png', 'mp4', 'mov', 'mkv', 'pdf', 'docx', 'zip']:
                fpath = os.path.join("medias", f"{msg_id}.{ext}")
                if os.path.exists(fpath):
                    uploader_files_total_size += os.path.getsize(fpath)
                    break
    uploader_files_total_size_mb = uploader_files_total_size / (1024*1024)
    stats_path = os.path.join("central_data", "stats.json")
    stats = {
        "uploader_files_total": uploader_files_total,
        "uploader_files_total_size_mb": uploader_files_total_size_mb
    }
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)

def periodic_stats_update(interval=300):
    import threading
    def loop():
        while True:
            update_uploader_stats()
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()

import subprocess
def safe_format(template_code, API_TOKEN="", OWNER_USER="", BOT_VERSION="4.2.4", BOT_CHILD_NAME=""):
    if not isinstance(template_code, str):
        raise TypeError("template_code must be str not Message object")
    out = template_code
    out = out.replace("{API_TOKEN}", API_TOKEN if API_TOKEN is not None else "")
    out = out.replace("{OWNER_USER}", str(OWNER_USER) if OWNER_USER is not None else "")
    out = out.replace("{BOT_VERSION}", BOT_VERSION if BOT_VERSION else "4.2.4")
    out = out.replace("{BOT_CHILD_NAME}", BOT_CHILD_NAME if BOT_CHILD_NAME else "")
    return out

def update_and_run_all_children_bots():
    """
    همه بچه‌ها رو با نسخه جدید baby_bot.py آپدیت و همیشه ران نگه می‌دارد.
    """
    logger.info("در حال خواندن قالب baby_bot.py ...")
    with open("baby_bot.py", "r", encoding="utf-8") as f:
        template_code = f.read()

    base = "."
    child_folders = []

    for folder in os.listdir(base):
        if folder.startswith("bot_") and os.path.isdir(folder):
            config_path = os.path.join(folder, "config.json")
            bot_path = os.path.join(folder, "bot.py")
            logger.info(f"[{folder}] بررسی پوشه بچه...")
            if not os.path.exists(config_path):
                logger.warning(f"[{folder}] فاقد config.json است، رد شد.")
                continue
            try:
                logger.info(f"[{folder}] خواندن config.json ...")
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if os.path.exists(bot_path):
                    logger.info(f"[{folder}] حذف bot.py قدیمی ...")
                    os.remove(bot_path)
                else:
                    logger.info(f"[{folder}] bot.py وجود نداشت، نیازی به حذف نبود.")
                api_token = cfg.get("API_TOKEN", "")
                bot_code = safe_format(
                    template_code,
                    API_TOKEN=api_token,
                    OWNER_USER=cfg.get("OWNER_USER", ""),
                    BOT_CHILD_NAME=cfg.get("BOT_CHILD_NAME", folder)
                )
                logger.info(f"[{folder}] در حال ساخت bot.py جدید ...")
                try:
                    with open(bot_path, "w", encoding="utf-8") as f2:
                        f2.write(bot_code)
                except Exception as e:
                    out = template_code
                    for k, v in cfg.items():
                        out = out.replace("{" + str(k) + "}", str(v))
                    with open(bot_path, "w", encoding="utf-8") as f2:
                        f2.write(out)
                logger.info(f"[{folder}] bot.py جدید ساخته شد.")
                child_folders.append(folder)
            except Exception as e:
                logger.error(f"❌ خطا در {folder}: {e}")

    def run_forever(folder):
        config_path = os.path.join(folder, "config.json")
        owner_id = None
        bot_name = folder
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                owner_id = cfg.get("OWNER_USER")
                bot_name = cfg.get("BOT_CHILD_NAME", folder)
        except:
            pass

        error_count = 0
        MAX_ERRORS = 10
        while True:
            try:
                logger.info(f"[{folder}] اجرای bot.py ...")
                proc = subprocess.Popen(
                    ["python3", "bot.py"],
                    cwd=folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                out, err = proc.communicate()
                logger.info(f"[{folder}] اجرا تمام شد. کد خروج: {proc.returncode}")
                # فقط اگر خطای واقعی برنامه بود اطلاع بده، نه توکن
                if err and owner_id:
                    msg = f"❌ خطا یا توقف در ربات بچه <b>{bot_name}</b>:\n<code>{err.decode('utf-8')[:3500]}</code>"
                    try:
                        bot.send_message(owner_id, msg, parse_mode="HTML")
                    except: pass

                if proc.returncode == 0:
                    error_count = 0
                else:
                    error_count += 1
                    if error_count >= MAX_ERRORS:
                        logger.error(f"[{folder}] اجرای bot.py بیش از {MAX_ERRORS} بار ارور داد. توقف اجرا تا رفع مشکل.")
                        if owner_id:
                            try:
                                bot.send_message(owner_id, f"❌ ربات بچه <b>{bot_name}</b> بیش از {MAX_ERRORS} بار کرش کرد! لطفاً رفع مشکل کنید.", parse_mode="HTML")
                            except: pass
                        break
                    time.sleep(30)
            except Exception as e:
                logger.error(f"❌ خطا در اجرای {folder}/bot.py: {e}")
                if owner_id:
                    try:
                        bot.send_message(owner_id, f"❌ اجرای ربات بچه <b>{bot_name}</b> ناموفق بود:\n<code>{str(e)}</code>", parse_mode="HTML")
                    except: pass
                time.sleep(30)

    for folder in child_folders:
        logger.info(f"شروع ترد اجرای دائمی برای {folder}")
        t = threading.Thread(target=run_forever, args=(folder,), daemon=True)
        t.start()

        
if __name__ == "__main__":
    logger.info("بات در حال شروع است...")
    try:
        bot.send_message(OWNER_ID, f"🤖 بات ران شد! نسخه: {BOT_VERSION}")
        logger.info(f"پیام 'بات ران شدم' به {OWNER_ID} ارسال شد.")
    except Exception as e:
        logger.error(f"خطا در ارسال پیام شروع بات: {e}")

    # این خط، همه بچه‌ها رو آپدیت و ران می‌کند:
    update_and_run_all_children_bots()

    super_stable_connection_monitor(bot, check_interval=5)

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("🛑 برنامه متوقف شد.")