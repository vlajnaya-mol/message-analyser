import emoji
import datetime
import itertools
from collections import Counter
from dateutil.relativedelta import relativedelta

MAX_MSG_LEN = 4096


def count_months(msgs):
    """Returns the number of months between first and last messages (calendar months)."""
    r = relativedelta(msgs[-1].date, msgs[0].date)
    return r.months + 12 * r.years


def get_filtered(msgs,
                 remove_empty=False,
                 remove_links=False,
                 remove_forwards=False,
                 except_patterns=None,
                 except_samples=None,
                 min_len=0,
                 max_len=MAX_MSG_LEN
                 ):
    """Filters a list of messages by different parameters.

    Notes:
        Patterns and samples are lowered as well as the messages they are compared to.

    Args:
        msgs (list of MyMessage objects): Messages to sort.
        remove_empty (bool): Skips/keeps messages with empty text component.
        remove_links (bool): Skips/keeps messages which are links.
        remove_forwards (bool): Skips/keeps messages which are forwarded.
        except_patterns (list of sets of strings (characters)):
            Skips messages which are made ONLY from the characters from any set in this list.
        except_samples (list of strings):
            Skips messages which are equal to any string in this list.
        min_len (int): Skips/keeps messages shorter than min_len.
        max_len (int): Skips/keeps messages longer than max_len.

    Returns:
        A list of MyMessage objects.
    """
    if except_patterns is not None:
        except_patterns = set(pattern.lower() for pattern in except_patterns)
    if except_samples is not None:
        except_samples = list(sample.lower() for sample in except_samples)
    return list(filter(lambda msg:
                       (not remove_empty or msg.text != "")
                       and min_len <= len(msg.text) <= max_len
                       and not (remove_forwards and msg.is_forwarded)
                       and not (remove_links and msg.is_link)
                       and (except_patterns is None or not any(set(msg.text.lower()) == p for p in except_patterns))
                       and (except_samples is None or not any(sample == msg.text for sample in except_samples)),
                       msgs))


def get_non_text_messages_grouped(groups):
    """Filters and structures messages for each group and non-text message type.

    Args:
        groups (list of lists of MyMessage objects): Messages grouped.

    Returns:
        A list of message types grouped:
        [
            {
                "groups": [list of numbers of specific messages in each group],
                "type": string type of these messages.
            }
        ]
    """
    return [
        {"groups": [len(list(filter(lambda m: m.has_audio, group))) for group in groups],
         "type": "audio"},
        {"groups": [len(list(filter(lambda m: m.has_voice, group))) for group in groups],
         "type": "voice"},
        {"groups": [len(list(filter(lambda m: m.has_photo, group))) for group in groups],
         "type": "photo"},
        {"groups": [len(list(filter(lambda m: m.has_video, group))) for group in groups],
         "type": "video"},
        {"groups": [len(list(filter(lambda m: m.has_sticker, group))) for group in groups],
         "type": "sticker"},
        {"groups": [len(list(filter(lambda m: m.is_link, group))) for group in groups],
         "type": "link"}
    ]


def get_response_speed_per_timedelta(msgs, name):
    """Gets list of response time lengths of a certain person.

    Notes:
        This function is not used anywhere (at the time when this docstring was written) because it needs
        better algorithm for making decisions about message being a response or not.

    Args:
        msgs (list of MyMessage objects): Messages.
        name (str): The name of the person whose response time is calculated.

    Returns:
        A a list of the person's (name) response time lengths.
    """
    res = []
    i = 0
    if msgs[0].author == name:
        while i < len(msgs) and msgs[i].author == name:
            i += 1
    while i < len(msgs):
        while i < len(msgs) and msgs[i].author != name:
            i += 1
        if i < len(msgs) and (msgs[i].date - msgs[i - 1].date).seconds <= 4 * 3600:  # because people sleep sometimes
            res.append((msgs[i].date - msgs[i - 1].date).seconds / 60)
        while i < len(msgs) and msgs[i].author == name:
            i += 1
    return res


def get_messages_per_timedelta(msgs, time_bin):
    """Gets lists of messages for each time interval with a given length. For example:
    time_bin is 7, so we will get lists of messages for each week between the first and last messages.

    Args:
        msgs (list of MyMessage objects): Messages.
        time_bin (int): The number of days in each bin (time interval).

    Returns:
        A dictionary such as:
            {
                day (datetime.date object): a list of messages within interval [day, day + time_bin)
            }
    """
    start_d = msgs[0].date.date()
    current_date = start_d
    end_d = msgs[-1].date.date()
    res = dict()
    while current_date <= end_d:
        res[current_date] = []
        current_date += relativedelta(days=time_bin)
    for msg in msgs:
        res[start_d + relativedelta(days=(msg.date.date() - start_d).days // time_bin * time_bin)].append(msg)
    return res


def get_months(msgs):
    """Gets months (first day for each month) between the first and the last messages in a list.

    Notes:
        ATTENTION: datetime objects have day parameter set to 1 (first day of the month) for EACH month.
    Args:
        msgs (list of Mymessage objects): Messages.

    Returns:
        A list of datetime.date objects.
    """
    start_d = msgs[0].date.date()
    end_d = msgs[-1].date.date()
    res = []
    month, year = start_d.month, start_d.year
    while (year < end_d.year or not month > end_d.month) and year <= end_d.year:
        res.append(datetime.date(year, month, 1))
        if month == 12:
            year += 1
            month = 0
        month += 1
    return res


def get_weeks(msgs):
    """Gets weeks (first day for each week) between the first and last messages in a list.

    Notes:
        First "week" is 7-days full.
        This function returns calendar weeks, not just 7-days intervals.
    Args:
        msgs (list of Mymessage objects): Messages.

    Returns:
        A list of datetime.date objects.
    """
    current_date = msgs[0].date.date()
    end_d = msgs[-1].date.date()
    res = []
    if current_date.weekday() != 0:
        current_date -= relativedelta(days=current_date.weekday())
    while current_date <= end_d:
        res.append(current_date)
        current_date += relativedelta(days=7)
    return res


def str_day(day):
    """Transforms datetime day object into a "%d/%m/%y" string.

    Args:
        day (datetime/datetime.date): Day.

    Returns:
        A "%d/%m/%y" string representation.
    """
    return day.strftime("%d/%m/%y")


def date_days_to_str_days(days):
    """Transforms a list of datetime objects into a list of "%d/%m/%y" strings.

    Args:
        days (list of datetime objects): Days.

    Returns:
        A list of "%d/%m/%y" days representations.
    """
    return [str_day(day) for day in days]


def str_month(month):
    """Transforms datetime month object into a "%m/%y" string.

        Args:
            month (datetime/datetime.date): Month.

        Returns:
            A "%m/%y" string representation.
        """
    return month.strftime("%m/%y")


def date_months_to_str_months(months):
    """Transforms a list of datetime objects into a list of "%m/%y" strings.

    Args:
        months (list of datetime objects): Months.

    Returns:
        A list of "%m/%y" months representations.
    """
    return [str_month(month) for month in months]


def get_messages_per_month(msgs):
    """Gets lists of messages for each month between the first and last message.

    Notes:
        Months keys are set to the first day of the month.

    Args:
        msgs (list of Mymessage objects): Messages.

    Returns:
        A dictionary such as:
            {
                month (datetime.date): list of messages within this month
            }
    """
    res = dict()
    current_date = msgs[0].date.date().replace(day=1)
    end_d = msgs[-1].date.date().replace(day=1)
    while current_date <= end_d:
        res[current_date] = []
        current_date += relativedelta(months=1)

    for msg in msgs:
        res[msg.date.date().replace(day=1)].append(msg)
    return res


def get_messages_per_week(msgs):
    """Gets lists of messages for each calendar week between the first and the last message.

    Args:
        msgs (list of Mymessage objects): Messages.

    Returns:
        A dictionary such as:
            {
                week (datetime.date): list of messages within this week
            }
    """
    res = dict()
    current_date = msgs[0].date.date()
    end_d = msgs[-1].date.date()
    if current_date.weekday() != 0:
        current_date -= relativedelta(days=current_date.weekday())
    while current_date <= end_d:
        res[current_date] = []
        current_date += relativedelta(days=7)

    for msg in msgs:
        res[msg.date.date() - relativedelta(days=msg.date.date().weekday())].append(msg)
    return res


def get_messages_per_minutes(msgs, minutes):
    """Gets lists of messages for each interval in minutes.

    Args:
        msgs (list of MyMessage objects): Messages.
        minutes (int): The number of minutes in one interval.

    Returns:
        A dictionary such as:
            {
                minute: list off all messages sent within interval [minute, minute + minutes).
            }
    """
    res = {i: [] for i in range(0, 24 * 60, minutes)}
    for msg in msgs:
        res[(msg.date.hour * 60 + msg.date.minute) // minutes * minutes].append(msg)
    return res


def get_messages_per_weekday(msgs):
    """Gets lists of messages for each day of the week (7 lists in a dictionary total).

    Args:
        msgs (list of MyMessage objects): Messages.

    Returns:
        A dictionary such as:
            {
                day_of_the_week (int 0-6): list off all messages sent on this day
            }
    """
    res = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for msg in msgs:
        res[msg.date.weekday()].append(msg)
    # placing Sunday at the end of the week # turned out we don't need it...
    # for i in [0, 1, 2, 3, 4, 5]:
    #     res[i], res[(i + 6) % 7] = res[(i + 6) % 7], res[i]
    return res


def get_messages_per_day(msgs):
    """Gets lists of messages for each day between the first and the last message.

    Notes:
        Days are stored in a dictionary as integers (first day is 0, second is 1 etc).

    Args:
        msgs (list of MyMessage objects): Messages.

    Returns:
        A dictionary such as:
            {
                day (int): list of messages sent this day
            }
    """
    current_date = msgs[0].date.date()
    end_d = msgs[-1].date.date()
    res = dict()
    one_day = relativedelta(days=1)
    while current_date <= end_d:
        res[current_date] = []
        current_date += one_day
    for msg in msgs:
        res[msg.date.date()].append(msg)
    return res


def get_hours():
    """Gets a list of str hours from 01:00 to 23:00"""
    return [f"{i:02d}:00" for i in range(24)]


def get_messages_per_hour(msgs):
    """Gets lists of messages for each hour of the day (total 24 lists).

    Args:
        msgs (list of MyMessage objects): Messages.

    Returns:
        A dictionary such as:
            {
                hour (string "%H:00"): list of messages sent this hour (for all days)
            }
    """
    res = {hour: [] for hour in get_hours()}
    for msg in msgs:
        res[f"{msg.date.hour:02d}:00"].append(msg)
    return res


def get_longest_pause(msgs):
    """Gets the longest time distance between two consecutive messages.

    Args:
        msgs (list of MyMessage objects): Messages.

    Returns:
        A tuple such as:
            (timedelta of the longest pause in a dialogue, start datetime of the pause, end datetime of the pause).
    """
    previous_date = msgs[0].date
    max_delta = datetime.datetime.today() - datetime.datetime.today()
    start_pause = end_pause = previous_date
    for msg in msgs[1:]:
        if msg.date - previous_date > max_delta:
            start_pause = previous_date
            end_pause = msg.date
            max_delta = msg.date - previous_date
        previous_date = msg.date
    return max_delta, start_pause, end_pause


def _tokenize(text, stem=False, filters=None):
    """Tokenizes a text into a list of tokens (words). Words are lowered, punctuation and digits are removed.

    Notes:
        filters example: ["NOUN", "ADJF", "VERB", "ADVB"].
        Stemming may work for ukrainian texts but now it is out-of-use.

    Args:
        text (str): A text to tokenize.
        stem (bool): True value means the words will be stemmed (currently out-of-use).
        filters (list of strings): List of string types of words (currently out-of-use).

    Returns:
        A list of words (strings).

    Raises:
        NotImplementedError: If you try to filter or stem.
    """
    # import pymorphy2
    # import pymorphy2_dicts_uk
    # morph = pymorphy2.MorphAnalyzer(lang='uk')
    i = 0
    words = []
    while i < len(text):
        word = ""
        while i < len(text) and (text[i].isalpha() or text[i] == '\'' or text[i] == '`'):
            word += text[i]
            i += 1
        if len(word) > 0:
            if stem or filters is not None:
                raise NotImplementedError
                # parsed = morph.parse(word.lower())[0]
                # if filters is None or any(el in parsed.tag for el in filters):
                #     words.append(parsed.normal_form)
            else:
                words.append(word.lower())
        i += 1
    return words


def get_words_countered(msgs, stem=False):
    """Counts all words in messages.

    Notes:
        Punctuation and digits are removed, words are lowered and countered.

    Args:
        msgs (list of MyMessage objects): Messages.
        stem (bool): True value means the words will be stemmed (currently out-of-use).

    Returns:
        collections.Counter of words.
    """
    return Counter(itertools.chain.from_iterable(_tokenize(msg.text, stem=stem) for msg in msgs))


def get_emoji_countered(msgs):
    """Counts all emojis in messages.

    Args:
        msgs (list of MyMessage objects): Messages.

    Returns:
        collections.Counter of emojis.
    """
    cnt = Counter()
    for msg in msgs:
        for character in msg.text:
            if character in emoji.UNICODE_EMOJI:
                cnt[character] += 1
    return cnt


def get_messages_lengths_countered(msgs):
    """Counts the length of each message.

    Args:
        msgs (list of MyMessage objects): Messages.

    Returns:
        collections.Counter of messages lengths.
    """
    return Counter([len(msg.text) for msg in msgs])
