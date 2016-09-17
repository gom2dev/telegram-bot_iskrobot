"""
 ISKRobot(Il-Su-KKun Robot) (일수꾼봇)

 Created by Gomgom (https://gomgom.io)
 Final released: 2016-09-17
 Version: v1.6.0
"""

#
# IMPORT PARTS
#
import sys
import os
import sqlite3
import random
import logging
from telegram.ext import Updater, CommandHandler
from telegram import Emoji, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardHide


#
# DEFINE PARTS
#
#
# exec has some information of commands and instructions
EXEC_LIST = (("일수", "[이름 금액 ... #내용]\n\t\t\t빚을 추가/변제(-)합니다.\n\t\t\t마지막에 '#내용' 추가 가능.\n\
                \t\t\t단, 태그는 띄어쓰기 불가."),
             ("더치", "[이름... 금액]\n\t\t\t비용을 1/n으로 나눠 추가합니다."),
             ("조회", "[ ]\n\t\t\t현재 빚 상황을 조회합니다."),
             ("명세", "[ ]\n\t\t\t최근 기록 내역을 조회합니다."),
             ("상환", "[이름 ...]\n\t\t\t목록을 삭제합니다."),
             ("계좌", "[정보]\n\t\t\t계좌주, 은행, 번호등을 추가합니다."),
             ("초기화", "[ ]\n\t\t\t모든 빚을 초기화합니다."))

# It's the location of DB file
FILE_LOCATION = os.path.dirname(__file__) + '/debt.db'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


#
# FUNCTION PARTS
#
#
# check_token() will perform input or update (if exists) TOKEN in DB
# Checking parameters is or not, if there is, it's put in TOKEN(It's token of this bot))
# Sample exec: python ISKRobot.py 12345678:A1B2C3D4E5F6G7H8i9_j10k11
def check_token():
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    cur.execute('SELECT COUNT(*) FROM t_admin')

    if len(sys.argv) > 2:  # arguments are weird
        print("인수 입력이 잘못되었습니다. 토큰만 입력이 가능합니다.")
        sys.exit()
    elif cur.fetchone()[0] == 0:  # if there isn't any token key on t_admin table
        if len(sys.argv) == 2:  # for input token key
            cur.execute('INSERT INTO t_admin VALUES("' + str(sys.argv[1]) + '")')
            con.commit()
            print("토큰 저장이 완료되었습니다. 봇을 시작합니다.")
            cur.execute('SELECT token_key FROM t_admin')
            result_token = str(cur.fetchone()[0])
            con.close()
            return result_token
        else:
            print("저장되어 있는 토큰이 없습니다. 매개변수에 TOKEN을 입력해 주세요.")
            sys.exit()
    else:  # if there is a token key on t_admin table
        if len(sys.argv) == 1:  # just start Il-su-kkun bot
            cur.execute('SELECT token_key FROM t_admin')
            result_token = str(cur.fetchone()[0])
            con.close()
            print("저장된 토큰을 사용합니다. 봇을 시작합니다.")
            return result_token
        else:  # update token key on DB
            cur.execute('UPDATE t_admin SET token_key="' + str(sys.argv[1]) + '"')
            con.commit()
            print("토큰이 업데이트 되었습니다. 봇을 시작합니다.")
            cur.execute('SELECT token_key FROM t_admin')
            result_token = str(cur.fetchone()[0])
            con.close()
            return result_token


# reset_db() will perform make DB if not exists
def reset_db():
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS t_admin (token_key text)")
    cur.execute("CREATE TABLE IF NOT EXISTS t_room (room_id text, owner text, account text, stopchecker int)")
    cur.execute("CREATE TABLE IF NOT EXISTS t_ledger (room_id text, name text, money int)")
    cur.execute("CREATE TABLE IF NOT EXISTS t_state (room_id text, command text, state text, date datetime)")
    con.commit()
    con.close()


# makeNumToMoney() will perform money will be shown like this (7500000 -> 7,500,000)
def make_num_to_money(money):
    result_number = ''
    origin_number = str(money)
    less_part_number = len(origin_number) % 3
    if len(origin_number) > 3:
        if less_part_number == 0:
            result_number = origin_number[:3]
            origin_number = origin_number[3:]
        else:
            result_number = origin_number[:less_part_number]
            origin_number = origin_number[less_part_number:]
        for i in range(0, len(origin_number) // 3):
            result_number += "," + origin_number[i * 3:(i * 3) + 3]
    else:
        result_number += origin_number
    return result_number


#
# BOT HANDLER PARTS
#
#
# It will show /start
def start(bot, update):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    start_message = '안녕하세요. 저는 일수꾼봇입니다. ' + Emoji.CAT_FACE_WITH_WRY_SMILE + '\n'
    start_message += '여러분들이 빌린 빚을 갚게 하려고 늘 노력하고 있답니다. :)\n'
    start_message += '도움말이 필요하시면 /help를 입력해 주세요. ^^'

    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0] == 0):
        cur.execute('INSERT INTO t_room VALUES("' + str(update.message.chat_id) + '", "' + str(
            update.message.from_user.id) + '", "", 0)')
        con.commit()
        con.close()
        return bot.sendMessage(update.message.chat_id, text=start_message +
                               '\n\n이 방에서 사용이 처음이시네요. 초기화 처리가 완료되었습니다.')
    else:
        con.close()
        return bot.sendMessage(update.message.chat_id,
                               text=start_message + '\n\n이미 이 채팅에는 관리자가 존재합니다.',
                               disable_notification=True)


# It will show /help
def support(bot, update):
    help_message = '*** 명령어 모음집 *** \n\n'
    for i in EXEC_LIST:
        help_message += ' - /' + i[0] + ' ' + i[1] + '\n'
    help_message += '\n' + ('*' * 19)

    bot.sendMessage(update.message.chat_id, text=help_message)


# It will be performed when you type, /일수 사람이름 금액
def add(bot, update, args):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check this chat room is registered, if not, just return
    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0]) == 0:
        return bot.sendMessage(update.message.chat_id,
                               text='* 이 방에서 초기화가 되지 않았습니다.\n/start를 통해 초기화 후 이용해 주세요. *',
                               disable_notification=True)
    # Check you're admin or not of this room
    cur.execute('SELECT owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if str(cur.fetchone()[0]) != str(update.message.from_user.id):
        return bot.sendMessage(update.message.chat_id, text='내 주인님이 아니에요..-_-+', disable_notification=True)

    for i in range(0, (len(args) // 2)):  # For Catching it's number or not
        try:
            int(args[(i * 2) + 1])  # Change String to Number for checking
        except ValueError:
            return bot.sendMessage(update.message.chat_id, text='금액에는 숫자만 입력할 수 있습니다.')
    if len(args) % 2 != 0 and str(args[-1])[0:1] != "#":  # Checking final thing is tag or not
        return bot.sendMessage(update.message.chat_id, text='올바르지 않은 입력입니다. /help를 참조해 주세요.')

    length = len(args)
    if len(args) % 2 == 1 and str(args[:-1])[0:1] == '#':
        length = len(args) - 1

    for i in range(0, length // 2):
        cur.execute('SELECT COUNT(*) FROM t_ledger WHERE room_id="' + str(update.message.chat_id) +
                    '" AND name="' + str(args[i * 2]) + '"')
        if int(cur.fetchone()[0]) != 0:
            cur.execute('SELECT money FROM t_ledger WHERE room_id="' + str(update.message.chat_id) +
                        '" AND name="' + str(args[i * 2]) + '"')
            current_money = int(cur.fetchone()[0])
            cur.execute('UPDATE t_ledger SET money=' + str(current_money + int(args[(i * 2) + 1])) +
                        ' WHERE room_id="' + str(update.message.chat_id) + '" AND name="' + str(args[i * 2]) + '"')
        else:
            cur.execute('INSERT INTO t_ledger VALUES("' + str(update.message.chat_id) + '", "' +
                        str(args[i * 2]) + '", "' + str(int(args[(i * 2) + 1])) + '")')
        cur.execute('SELECT money FROM t_ledger WHERE room_id="' + str(update.message.chat_id) + '" and name="'
                    + str(args[i * 2]) + '"')
        current_money = int(cur.fetchone()[0])
        if current_money == 0:
            cur.execute('DELETE FROM t_ledger WHERE room_id="' + str(update.message.chat_id) + '" AND name="' +
                        str(args[i]) + '"')

    cur.execute('INSERT INTO t_state VALUES("' + str(update.message.chat_id) + '", "일수", "' +
                str(args[0:]) + '", date("now","localtime"))')

    reply_markup = ReplyKeyboardHide()

    bot.sendMessage(update.message.chat_id, text='추가가 완료되었습니다.', reply_markup=reply_markup)

    con.commit()
    con.close()


# It will divide big money per persons, to use /더치 [사람 목록] [비용]
def dutch(bot, update, args):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check this chat room is registered, if not, just return
    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0]) == 0:
        return bot.sendMessage(update.message.chat_id,
                               text='* 이 방에서 초기화가 되지 않았습니다.\n/start를 통해 초기화 후 이용해 주세요. *',
                               disable_notification=True)
    # Check you're admin or not of this room
    cur.execute('SELECT owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if str(cur.fetchone()[0]) != str(update.message.from_user.id):
        return bot.sendMessage(update.message.chat_id, text='내 주인님이 아니에요..-_-+', disable_notification=True)

    try:
        target_money = int(args[len(args) - 1])  # Change String(target money) to Number for checking
    except ValueError:
        return bot.sendMessage(update.message.chat_id, text='금액에는 숫자만 입력할 수 있습니다.')

    persons = args[0:len(args) - 1]
    person_number = len(persons)
    person_list = ''

    if target_money % person_number == 0:  # If I can divide my money exactly,
        for i in range(0, person_number):
            person_list += str(persons[i]) + ' ' + str(int(target_money / person_number)) + ' '  # Just Input money
        custom_keyboard = [[KeyboardButton("/일수 " + person_list), KeyboardButton('/cancel')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard='True')
        return bot.sendMessage(update.message.chat_id, text='다음과 같이 입력하시겠습니까?', reply_markup=reply_markup)
    else:  # If I can't,
        temp_money = round(target_money / person_number, -2)
        if (target_money - temp_money) % (person_number - 1) == 0:
            specialist = str(persons[random.randint(0, person_number - 1)])  # Pick one for taking little profit
            person_list += specialist + ' ' + str(int(temp_money)) + ' '  # And Input profit person,
            persons.remove(specialist)
            for i in range(0, (person_number - 1)):  # add other persons,
                person_list += str(persons[i]) + ' ' + str(int((target_money - temp_money) / (person_number - 1))) + ' '
            custom_keyboard = [[KeyboardButton("/일수 " + person_list), KeyboardButton('/cancel')]]
            reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard='True')
            return bot.sendMessage(update.message.chat_id, text='다음과 같이 입력하시겠습니까?',
                                   reply_markup=reply_markup)


# It will be performed when you type, /조회
def view(bot, update):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check this chat room is registered, if not, just return
    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0]) == 0:
        return bot.sendMessage(update.message.chat_id,
                               text='* 이 방에서 초기화가 되지 않았습니다.\n/start를 통해 초기화 후 이용해 주세요. *',
                               disable_notification=True)

    cur.execute('SELECT * FROM t_ledger WHERE room_id="' + str(update.message.chat_id) + '" ORDER BY money desc')
    fetched_list = cur.fetchall()

    result = "\n\n" + ("*" * 19) + "\n"
    for i in range(len(fetched_list)):
        result += str(fetched_list[i][1]) + " " + make_num_to_money((fetched_list[i][2])) + "원\n"
    result += "*" * 19

    cur.execute('SELECT account FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    result += "\n[" + str(cur.fetchone()[0]) + "]"

    cur.execute('SELECT * FROM t_state WHERE room_id="' + str(update.message.chat_id) + '" ORDER BY date desc limit 1')
    try:
        bot.sendMessage(update.message.chat_id, text='잔금 조회입니다. (' + str(cur.fetchone()[3])[5:] + ' 기준)' +
                        result, disable_notification=True)
    except TypeError:
        bot.sendMessage(update.message.chat_id, text='보여드릴 조회/내역이 없습니다.', disable_notification=True)
    con.close()


# It will be performed when you type, /명세, it shows your states.
def latest(bot, update):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check this chat room is registered, if not, just return
    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0]) == 0:
        return bot.sendMessage(update.message.chat_id,
                               text='* 이 방에서 초기화가 되지 않았습니다.\n/start를 통해 초기화 후 이용해 주세요. *',
                               disable_notification=True)

    # Get latest list of your statements (limit 10)
    cur.execute('SELECT * FROM t_state WHERE room_id="' + str(update.message.chat_id) + '" ORDER BY date desc limit 10')
    fetched_list = cur.fetchall()

    result = "\n\n" + ("#" * 19) + "\n"
    for i in range(len(fetched_list)):
        result += '[' + str(fetched_list[i][1]) + '] '
        for j in range(1, len(fetched_list[i][2]) - 1):  # For Removing '[', ']'(in loop checker), "'", ','(in loop)
            if str(fetched_list[i][2][j]) == "'" or str(fetched_list[i][2][j]) == ",":
                continue
            else:
                result += str(fetched_list[i][2][j])
        result += '\n'
    result += "#" * 19

    cur.execute('SELECT * FROM t_state WHERE room_id="' + str(update.message.chat_id) + '" ORDER BY date desc limit 1')
    try:
        bot.sendMessage(update.message.chat_id, text='최근 명세서입니다. (' + str(cur.fetchone()[3])[5:] + ' 기준)' +
                        result, disable_notification=True)
    except TypeError:
        bot.sendMessage(update.message.chat_id, text='보여드릴 조회/내역이 없습니다.', disable_notification=True)
    con.close()


# It will be performed when you type, /상환 사람이름
def remove(bot, update, args):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check this chat room is registered, if not, just return
    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0]) == 0:
        return bot.sendMessage(update.message.chat_id,
                               text='* 이 방에서 초기화가 되지 않았습니다.\n/start를 통해 초기화 후 이용해 주세요. *',
                               disable_notification=True)
    # Check you're admin or not of this room
    cur.execute('SELECT owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if str(cur.fetchone()[0]) != str(update.message.from_user.id):
        return bot.sendMessage(update.message.chat_id, text='내 주인님이 아니에요..-_-+', disable_notification=True)

    cur.execute('SELECT name FROM t_ledger WHERE room_id="' + str(update.message.chat_id) + '"')
    fetched_list = cur.fetchall()

    for i in range(len(args)):
        counter = 0
        for j in range(len(fetched_list)):
            if str(fetched_list[j][0]) == str(args[i]):
                cur.execute('DELETE FROM t_ledger WHERE room_id="' + str(update.message.chat_id) + '" AND name="' +
                            str(args[i]) + '"')
                counter = 1
        if counter == 1:
            bot.sendMessage(update.message.chat_id, text='%s(이)에 대한 전체 상환이 완료되었습니다.' % str(args[i]))
        else:
            bot.sendMessage(update.message.chat_id, text='%s은(는) 존재하지 않습니다. 다시 확인해 주세요.' % str(args[i]))

    cur.execute('INSERT INTO t_state VALUES("' + str(update.message.chat_id) + '", "상환", "' +
                str(args[0:]) + '", date("now","localtime"))')

    con.commit()
    con.close()


# It will be performed when you type, /초기화
def reset(bot, update):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check this chat room is registered, if not, just return
    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0]) == 0:
        return bot.sendMessage(update.message.chat_id,
                               text='* 이 방에서 초기화가 되지 않았습니다.\n/start를 통해 초기화 후 이용해 주세요. *',
                               disable_notification=True)
    # Check you're admin or not of this room
    cur.execute('SELECT owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if str(cur.fetchone()[0]) != str(update.message.from_user.id):
        return bot.sendMessage(update.message.chat_id, text='내 주인님이 아니에요..-_-+', disable_notification=True)

    cur.execute('DELETE FROM t_ledger WHERE room_id="' + str(update.message.chat_id) + '"')

    cur.execute('INSERT INTO t_state VALUES("' + str(update.message.chat_id) + '", "초기화", "' + ' 처리되었습니다.' +
                '", date("now","localtime"))')

    bot.sendMessage(update.message.chat_id, text='초기화 작업을 완료했습니다.')

    con.commit()
    con.close()


# It will perform write account status on every '/조회'
def account(bot, update, args):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check this chat room is registered, if not, just return
    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0]) == 0:
        return bot.sendMessage(update.message.chat_id,
                               text='* 이 방에서 초기화가 되지 않았습니다.\n/start를 통해 초기화 후 이용해 주세요. *',
                               disable_notification=True)
    # Check you're admin or not of this room
    cur.execute('SELECT owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if str(cur.fetchone()[0]) != str(update.message.from_user.id):
        return bot.sendMessage(update.message.chat_id, text='내 주인님이 아니에요..-_-+', disable_notification=True)

    account_data = ''
    for i in range(0, len(args)):
        account_data += str(args[i]) + ' '
    account_data = account_data[:-1]

    cur.execute('UPDATE t_room SET account="' + account_data + '" WHERE room_id="' + str(update.message.chat_id) + '"')
    bot.sendMessage(update.message.chat_id, text='계좌가 기록되었습니다.', disable_notification=True)

    con.commit()
    con.close()


def stop(bot, update):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check this chat room is registered, if not, just return
    cur.execute('SELECT COUNT(*) FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if int(cur.fetchone()[0]) == 0:
        return bot.sendMessage(update.message.chat_id,
                               text='* 이 방에서 초기화가 되지 않았습니다.\n/start를 통해 초기화 후 이용해 주세요. *',
                               disable_notification=True)
    # Check you're admin or not of this room
    cur.execute('SELECT owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if str(cur.fetchone()[0]) != str(update.message.from_user.id):
        return bot.sendMessage(update.message.chat_id, text='내 주인님이 아니에요..-_-+', disable_notification=True)

    cur.execute('SELECT stopchecker FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')

    if int(cur.fetchone()[0]) == 0:
        cur.execute('UPDATE t_room SET stopchecker=1 WHERE room_id="' + str(update.message.chat_id) + '"')
        con.commit()

        custom_keyboard = [[KeyboardButton("/confirm"), KeyboardButton("/cancel")]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard='True')
        bot.sendMessage(update.message.chat_id, text='정말로 사용을 정지하시겠습니까?', reply_markup=reply_markup)

    con.close()


def confirm(bot, update):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check you're admin or not of this room
    cur.execute('SELECT owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if str(cur.fetchone()[0]) != str(update.message.from_user.id):
        return

    cur.execute('SELECT stopchecker, owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    fetched_list = cur.fetchone()

    if int(fetched_list[0]) == 1 and str(fetched_list[1]) == str(update.message.from_user.id):
        cur.execute('DELETE FROM t_ledger WHERE room_id="' + str(update.message.chat_id) + '"')
        cur.execute('DELETE FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
        con.commit()
        con.close()
        reply_markup = ReplyKeyboardHide()
        return bot.sendMessage(chat_id=update.message.chat_id,
                               text='이용을 중지합니다. 감사합니다.\n재이용은 다시 /start를 입력해 주세요.',
                               reply_markup=reply_markup)


def cancel(bot, update):
    # Connect to DB file
    con = sqlite3.connect(FILE_LOCATION)
    cur = con.cursor()

    # Check you're admin or not of this room
    cur.execute('SELECT owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    if str(cur.fetchone()[0]) != str(update.message.from_user.id):
        return

    # I just comment it (Because I think it's not necessary)
    # cur.execute('SELECT stopchecker, owner FROM t_room WHERE room_id="' + str(update.message.chat_id) + '"')
    # fetched_list = cur.fetchone()

    cur.execute('UPDATE t_room SET stopchecker=0 WHERE room_id="' + str(update.message.chat_id) + '"')
    con.commit()
    con.close()
    reply_markup = ReplyKeyboardHide()
    return bot.sendMessage(chat_id=update.message.chat_id, text='취소되었습니다.', reply_markup=reply_markup,
                           disable_notification=True)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


#
# MAIN PARTS
#
# It is main function of this program
def main():
    # Reset Databases
    reset_db()

    # Check Token key for start bot
    TOKEN = check_token()

    # Make Telegram bot updater
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", support))
    dp.add_handler(CommandHandler(EXEC_LIST[0][0], add, pass_args=True))
    dp.add_handler(CommandHandler(EXEC_LIST[1][0], dutch, pass_args=True))
    dp.add_handler(CommandHandler(EXEC_LIST[2][0], view))
    dp.add_handler(CommandHandler(EXEC_LIST[3][0], latest))
    dp.add_handler(CommandHandler(EXEC_LIST[4][0], remove, pass_args=True))
    dp.add_handler(CommandHandler(EXEC_LIST[5][0], account, pass_args=True))
    dp.add_handler(CommandHandler(EXEC_LIST[6][0], reset))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("confirm", confirm))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
