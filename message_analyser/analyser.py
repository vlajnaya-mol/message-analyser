import os
import asyncio
import datetime
import message_analyser.plotter as plt
import message_analyser.storage as storage
import message_analyser.retriever.vkOpt as vkOpt
import message_analyser.structure_tools as stools
import message_analyser.retriever.telegram as tlg
from message_analyser.misc import log_line, delay


async def save_scalar_info(msgs, your_name, target_name, dir_path):
    """Saves scalar information about messages into a file. Additionally prints all the info to console.

    Args:
        msgs (list of MyMessage objects): Messages.
        your_name (str): Your name.
        target_name (str): Target's name.
        dir_path (str): A path to the file to store info in.
    """
    with open(dir_path + "/scalar_info.csv", 'w', encoding="utf-8") as fp:
        day_messages = stools.get_messages_per_day(msgs)

        print_func = log_line

        fp.write(f"Start date:,{msgs[0].date}\n")
        print_func(f"{'Start date:'.ljust(25)}{msgs[0].date}")

        fp.write(f"Duration:,{str(msgs[-1].date - msgs[0].date).replace(',',' ')}\n")
        print_func(f"{'Duration:'.ljust(25)}{msgs[-1].date - msgs[0].date}")

        empty_days_num = len([day for day in day_messages if not day_messages[day]])
        fp.write(f"Days without messages:,{empty_days_num},\n")
        print_func(f"{'Days without messages:'.ljust(25)}{empty_days_num}")

        most_active = max(day_messages, key=lambda day: len(day_messages[day]))
        fp.write(f"Most active day:,{most_active} : {len(day_messages[most_active])} messages\n")
        print_func(f"{'Most active day:'.ljust(25)}{most_active} : {len(day_messages[most_active])} messages")

        average = len(msgs) / len(day_messages)
        fp.write(f"Average messages per day:,{average:.2f} messages\n")
        print_func(f"{'Average messages per day:'.ljust(25)}{average:.2f} messages")

        max_delta, start_pause, end_pause = stools.get_longest_pause(msgs)
        fp.write(f"Longest pause:,{str(max_delta).replace(',',' ')} From {start_pause} to {end_pause}\n")
        print_func(f"{'Longest pause:'.ljust(25)}{max_delta} From {start_pause} to {end_pause}")

        fp.write(f"\nINFO,TOTAL,{your_name},{target_name}\n")
        print_func(f"{'INFO'.ljust(20)}{'TOTAL'.ljust(15)}{your_name:<15s}{target_name:<15s}")

        total_num = len(msgs)
        target_num = len([msg for msg in msgs if msg.author == target_name])
        fp.write(f"All messages,{total_num},{total_num-target_num},{target_num}\n")
        print_func(f"{'All messages'.ljust(20)}{total_num:<15d}{total_num-target_num:<15d}{target_num:<15d}")

        msgs = stools.get_filtered(msgs, remove_forwards=True, remove_links=True, max_len=4095)

        total_chars = sum([len(msg.text) for msg in msgs if not msg.is_forwarded])
        target_chars = sum([len(msg.text) for msg in msgs if not msg.is_forwarded and msg.author == target_name])
        fp.write(f"Characters,{total_chars},{total_chars-target_chars},{target_chars}\n")
        print_func(f"{'Characters'.ljust(20)}{total_chars:<15d}{total_chars-target_chars:<15d}{target_chars:<15d}")

        total_photos = len([msg for msg in msgs if msg.has_photo])
        target_photos = len([msg for msg in msgs if msg.has_photo and msg.author == target_name])
        fp.write(f"Photos,{total_photos},{total_photos-target_photos},{target_photos}\n")
        print_func(f"{'Photos'.ljust(20)}{total_photos:<15d}{total_photos-target_photos:<15d}{target_photos:<15d}")

        total_stickers = len([msg for msg in msgs if msg.has_sticker])
        target_stickers = len([msg for msg in msgs if msg.has_sticker and msg.author == target_name])
        fp.write(f"Stickers,{total_stickers},{total_stickers-target_stickers},{target_stickers}\n")
        print_func((f"{'Stickers'.ljust(20)}{total_stickers:<15d}{total_stickers-target_stickers:<15d}"
                    f"{target_stickers:<15d}"))

        total_songs = len([msg for msg in msgs if msg.has_audio])
        target_songs = len([msg for msg in msgs if msg.has_audio and msg.author == target_name])
        fp.write(f"Songs (audio files),{total_songs},{total_songs-target_songs},{target_songs}\n")
        print_func((f"{'Songs (audio files)'.ljust(20)}{total_songs:<15d}{total_songs-target_songs:<15d}"
                    f"{target_songs:<15d}"))

        total_voice = len([msg for msg in msgs if msg.has_voice])
        target_voice = len([msg for msg in msgs if msg.has_voice and msg.author == target_name])
        fp.write(f"Voice messages,{total_voice},{total_voice-target_voice},{target_voice}\n")
        print_func(f"{'Voice messages'.ljust(20)}{total_voice:<15d}{total_voice-target_voice:<15d}{target_voice:<15d}")

        total_video = len([msg for msg in msgs if msg.has_video])
        target_video = len([msg for msg in msgs if msg.has_video and msg.author == target_name])
        fp.write(f"Video messages,{total_video},{total_video-target_video},{target_video}\n")
        print_func(f"{'Video messages'.ljust(20)}{total_video:<15d}{total_video-target_video:<15d}{target_video:<15d}")

    log_line(f"Scalar info was saved into {dir_path}/scalar_info.csv file.")


async def _plot_messages_distribution(msgs, your_name, target_name, results_directory):
    """Shows how messages are distributed."""
    plt.heat_map(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.pie_messages_per_author(msgs, your_name, target_name, results_directory)
    await asyncio.sleep(delay)
    plt.stackplot_non_text_messages_percentage(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.barplot_non_text_messages(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.barplot_messages_per_weekday(msgs, your_name, target_name, results_directory)
    await asyncio.sleep(delay)
    plt.barplot_messages_per_day(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.barplot_messages_per_minutes(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.barplot_non_text_messages(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.distplot_messages_per_hour(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.distplot_messages_per_month(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.distplot_messages_per_day(msgs, results_directory)
    await asyncio.sleep(delay)
    plt.lineplot_messages(msgs, your_name, target_name, results_directory)
    await asyncio.sleep(delay)
    log_line("Messages distribution was analysed.")


async def _plot_messages_distribution_content_based(msgs, your_name, target_name, results_directory):
    """Shows how some characteristics of messages content are distributed."""
    plt.lineplot_message_length(msgs, your_name, target_name, results_directory)
    await asyncio.sleep(delay)
    plt.barplot_emojis(msgs, your_name, target_name, 10, results_directory)
    await asyncio.sleep(delay)
    log_line("Content based messages distribution was analysed.")


async def _plot_words_distribution(msgs, your_name, target_name, results_directory, words):
    """Shows how some words are distributed among the users."""
    plt.barplot_words(msgs, your_name, target_name, words, 10, results_directory)
    await asyncio.sleep(delay)
    plt.wordcloud(msgs, words, results_directory)
    await asyncio.sleep(delay)
    log_line("Words distribution was analysed.")


async def _plot_all(msgs, your_name, target_name, results_directory, words_file):
    await save_scalar_info(msgs, your_name, target_name, results_directory)
    await asyncio.sleep(delay)
    await _plot_messages_distribution(msgs, your_name, target_name, results_directory)
    await asyncio.sleep(delay)

    filtered_msgs = stools.get_filtered(msgs, remove_forwards=True, remove_empty=True, remove_links=True, max_len=4095)

    await _plot_messages_distribution_content_based(filtered_msgs, your_name, target_name, results_directory)
    await asyncio.sleep(delay)
    if words_file:
        words = storage.get_words(words_file)
        if words:
            await _plot_words_distribution(filtered_msgs, your_name, target_name, results_directory, words)
        await asyncio.sleep(delay)


async def _get_all_messages(dialog, vkopt_file, your_name, target_name, loop):
    msgs = []
    if dialog != -1:
        msgs.extend(await tlg.get_telegram_messages(your_name, target_name, loop=loop, target_id=dialog))
    await  asyncio.sleep(delay)
    if vkopt_file:
        msgs.extend(vkOpt.get_mymessages_from_file(your_name, target_name, vkopt_file))
    await  asyncio.sleep(delay)
    if dialog != -1 and vkopt_file:
        msgs.sort(key=lambda msg: msg.date)
    await  asyncio.sleep(delay)
    return msgs


def _save_words(msgs, your_name, target_name, path):
    total_words_cnt = stools.get_words_countered(msgs)
    top_words = [w for w, c in total_words_cnt.most_common(1000)]
    your_words_cnt = stools.get_words_countered([msg for msg in msgs if msg.author == your_name])
    target_words_cnt = stools.get_words_countered([msg for msg in msgs if msg.author == target_name])
    storage.store_top_words_count(top_words, your_words_cnt, target_words_cnt, path)


async def _analyse(msgs, your_name, target_name, words_file, store_msgs=True, store_words=True):
    """Does analysis and stores results."""
    log_line("Start messages analysis process.")

    if not len(msgs):
        log_line("No messages were received.")
        return
    date = datetime.datetime.today().strftime('%d-%m-%y %H-%M-%S')
    results_directory = os.path.join(os.path.split(os.path.normpath(os.path.dirname(__file__)))[0], "results",
                                     f"{date}_{your_name}_{target_name}")

    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    await asyncio.sleep(delay)

    if store_msgs:
        file_with_msgs = "messages.txt"
        storage.store_msgs(os.path.join(results_directory, file_with_msgs), msgs)
    if store_words:
        file_with_words = "words.txt"
        _save_words(msgs, your_name, target_name, os.path.join(results_directory, file_with_words))

    await asyncio.sleep(delay)

    await _plot_all(msgs, your_name, target_name, results_directory, words_file)

    log_line("Done.")


def analyse_from_file(path):
    """Analyses messages from a single file which was previously created by this program.

    Notes:
        Requires all the necessary configuration parameters (config.ini file) to be set either by GUI or manually.
    """
    _, _, words_file, your_name, target_name = storage.get_session_params()
    msgs = storage.get_msgs(path)
    asyncio.get_event_loop().run_until_complete(_analyse(msgs, your_name, target_name, words_file, store_msgs=False))


async def retrieve_and_analyse(loop):
    """(async) Analyses messages from VkOpt file and/or Telegram dialogue.

    Notes:
        Requires all the necessary configuration parameters (config.ini file) to be set either by GUI or manually.
    """
    dialog, vkopt_file, words_file, your_name, target_name = storage.get_session_params()
    msgs = await _get_all_messages(dialog, vkopt_file, your_name, target_name, loop)
    await _analyse(msgs, your_name, target_name, words_file)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(retrieve_and_analyse(asyncio.get_event_loop()))
