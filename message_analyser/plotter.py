import os
import emoji
import random
import operator
import numpy as np
import pandas as pd
import seaborn as sns
import wordcloud as wc
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.colors as mpl_colors
import message_analyser.structure_tools as stools
from message_analyser.misc import avg, log_line, months_border


def _change_bar_width(ax, new_value):
    # https://stackoverflow.com/a/44542112
    for patch in ax.patches:
        current_width = patch.get_width()
        diff = current_width - new_value

        # we change the bar width
        patch.set_width(new_value)

        # we recenter the bar
        patch.set_x(patch.get_x() + diff * .5)


def heat_map(msgs, path_to_save, seasons=False):
    sns.set(style="whitegrid")

    messages_per_day = stools.get_messages_per_day(msgs)
    months = stools.date_months_to_str_months(stools.get_months(msgs))
    heat_calendar = {month: np.array([None] * 31, dtype=np.float64) for month in months}
    for day, d_msgs in messages_per_day.items():
        heat_calendar[stools.str_month(day)][day.day - 1] = len(d_msgs)

    # min_day = len(min(messages_per_day.values(), key=len))
    max_day = len(max(messages_per_day.values(), key=len))

    data = np.array(list(heat_calendar.values()))
    mask = np.array([np.array(arr, dtype=bool) for arr in data])

    cmap = cm.get_cmap("Purples")

    center = max_day * 0.4  # (avg([len(d) for d in messages_per_day.values()]) + (max_day - min_day) / 2) / 2

    ax = sns.heatmap(data=data, cmap=cmap, center=center, xticklabels=True, yticklabels=True,
                     square=True, linewidths=.2, cbar_kws={"shrink": .5})

    # builds a mask to highlight empty days
    sns.heatmap(data, mask=mask,
                xticklabels=range(1, 32),
                yticklabels=months,
                linewidths=.2, cbar=False, cmap=mpl_colors.ListedColormap(["#ffffe6"]))

    if seasons:  # divides heatmap on seasons
        season_lines = [i for i, m in enumerate(months) if m.month % 3 == 0 and i != 0]
        ax.hlines(season_lines, *ax.get_xlim(), colors=["b"])
    ax.set(xlabel='day', ylabel="month")
    ax.margins(x=0)

    plt.tight_layout()
    fig = plt.gcf()
    fig.set_size_inches(11, 8)
    fig.savefig(os.path.join(path_to_save, heat_map.__name__ + ".png"), dpi=600)

    # plt.show()
    plt.close("all")
    log_line(f"{heat_map.__name__} was created.")


def pie_messages_per_author(msgs, your_name, target_name, path_to_save):
    forwarded = len([msg for msg in msgs if msg.is_forwarded])
    msgs = list(filter(lambda msg: not msg.is_forwarded, msgs))
    your_messages_len = len([msg for msg in msgs if msg.author == your_name])
    target_messages_len = len(msgs) - your_messages_len
    data = [your_messages_len, target_messages_len, forwarded]
    labels = [f"{your_name}\n({your_messages_len})",
              f"{target_name}\n({target_messages_len})",
              f"forwarded\n({forwarded})"]
    explode = (.0, .0, .2)

    fig, ax = plt.subplots(figsize=(13, 8), subplot_kw=dict(aspect="equal"))

    wedges, _, autotexts = ax.pie(x=data, explode=explode, colors=["#4982BB", "#5C6093", "#53B8D7"],
                                  autopct=lambda pct: f"{pct:.1f}%",
                                  wedgeprops={"edgecolor": "black", "alpha": 0.8})

    ax.legend(wedges, labels,
              loc="upper right",
              bbox_to_anchor=(1, 0, 0.5, 1))

    plt.setp(autotexts, size=10, weight="bold")

    fig.savefig(os.path.join(path_to_save, pie_messages_per_author.__name__ + ".png"), dpi=600)
    # plt.show()
    plt.close("all")
    log_line(f"{pie_messages_per_author.__name__} was created.")


def _get_xticks(msgs, crop=True):
    start_date = msgs[0].date.date()
    xticks = []
    months_num = stools.count_months(msgs)
    if months_num > months_border:
        xlabel = "month"
        months_ticks = stools.get_months(msgs)
        xticks_labels = stools.date_months_to_str_months(months_ticks)
        if (months_ticks[1] - start_date).days < 10 and crop:
            xticks_labels[0] = ""  # remove first short month tick for better look
        for month in months_ticks:
            xticks.append(max(0, (month - start_date).days))
            # it has max because start date is usually later than first month date.
    else:  # too short message history -> we split data by weeks, not months
        xlabel = "week"
        weeks_ticks = stools.get_weeks(msgs)
        xticks_labels = stools.date_days_to_str_days(weeks_ticks)
        if len(weeks_ticks) > 2 and (weeks_ticks[1] - start_date).days < 3 and crop:
            xticks_labels[0] = ""  # remove first short week tick for better look
        for date in weeks_ticks:
            xticks.append(max(0, (date - start_date).days))
            #  it has max because start date is usually later than first week date.

    return xticks, xticks_labels, xlabel


def _get_plot_data(msgs):
    """Gets grouped data to plot.

    Returns:
        x, y (tuple):
            x is a list of values for the x axis.
            y is a list of groups of messages (for y axis).
    """
    start_date = msgs[0].date.date()
    end_date = msgs[-1].date.date()
    xticks = []
    months_num = stools.count_months(msgs)
    if months_num > months_border:
        messages_per_month = stools.get_messages_per_month(msgs)
        months_ticks = list(messages_per_month.keys())
        for month in months_ticks:
            xticks.append(max(0, (month - start_date).days))
            # it has max because start date is usually later than first month date.
        y = list(messages_per_month.values())
    else:  # too short message history -> we split data by weeks, not months
        messages_per_week = stools.get_messages_per_week(msgs)
        days_ticks = messages_per_week.keys()
        for date in days_ticks:
            xticks.append(max(0, (date - start_date).days))
            #  it has max because start date is usually later than first week date.
        y = list(messages_per_week.values())

    # put x values at the middle of each bar (bin)
    x = [(xticks[i] + xticks[i + 1]) / 2 for i in range(1, len(xticks) - 1)]
    # except for the first and the last values
    x.insert(0, xticks[0])
    if len(y) > 1:
        x.append((xticks[-1] + (end_date - start_date).days) / 2)

    return x, y


def stackplot_non_text_messages_percentage(msgs, path_to_save):
    sns.set(style="whitegrid", palette="muted")

    colors = ['y', 'b', 'c', 'r', 'g', 'm']

    (x, y_total), (xticks, xticks_labels, xlabel) = _get_plot_data(msgs), _get_xticks(msgs)

    stacks = stools.get_non_text_messages_grouped(y_total)

    # Normalize values
    for i in range(len(stacks[0]["groups"])):
        total = sum(stack["groups"][i] for stack in stacks)
        for stack in stacks:
            if not total:
                stack["groups"][i] = 0
            else:
                stack["groups"][i] /= total

    plt.stackplot(x, *[stack["groups"] for stack in stacks], labels=[stack["type"] for stack in stacks],
                  colors=colors, alpha=0.7)

    plt.margins(0, 0)
    plt.xticks(xticks, rotation=65)
    plt.yticks([i / 10 for i in range(0, 11, 2)])

    ax = plt.gca()
    ax.set_xticklabels(xticks_labels)
    ax.set_yticklabels([f"{i}%" for i in range(0, 101, 20)])
    ax.tick_params(axis='x', bottom=True, color="#A9A9A9")
    ax.set(xlabel=xlabel, ylabel="non-text messages")

    # https://stackoverflow.com/a/4701285
    # Shrink current axis by 10%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    # Put a legend to the right of the current axis
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    fig = plt.gcf()
    fig.set_size_inches(11, 8)

    fig.savefig(os.path.join(path_to_save, stackplot_non_text_messages_percentage.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{stackplot_non_text_messages_percentage.__name__} was created.")
    plt.close("all")


def barplot_non_text_messages(msgs, path_to_save):
    sns.set(style="whitegrid", palette="muted")

    colors = ['y', 'b', 'c', 'r', 'g', 'm']

    (x, y_total), (xticks, xticks_labels, xlabel) = _get_plot_data(msgs), _get_xticks(msgs, crop=False)

    bars = stools.get_non_text_messages_grouped(y_total)

    # bars are overlapping, so firstly we need to sum up the all...
    sum_bars = [0] * len(y_total)
    for bar in bars:
        sum_bars = list(map(operator.add, sum_bars, bar["groups"]))
    # ... plot and subtract one by one.
    for i, bar in enumerate(bars[:-1]):
        sns.barplot(x=xticks_labels, y=sum_bars, label=bar["type"], color=colors[i])
        sum_bars = list(map(operator.sub, sum_bars, bar["groups"]))
    ax = sns.barplot(x=xticks_labels, y=sum_bars, label=bars[-1]["type"], color=colors[-1])
    _change_bar_width(ax, 1.)

    # https://stackoverflow.com/a/4701285
    # Shrink current axis by 10%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    # Put a legend to the right of the current axis
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    ax.set_xticklabels(xticks_labels, ha="right")
    ax.set(xlabel=xlabel, ylabel="messages")

    plt.xticks(rotation=65)
    fig = plt.gcf()
    fig.set_size_inches(16, 8)

    fig.savefig(os.path.join(path_to_save, barplot_non_text_messages.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{barplot_non_text_messages.__name__} was created.")
    plt.close("all")


def barplot_messages_per_day(msgs, path_to_save):
    sns.set(style="whitegrid", palette="muted")
    sns.despine(top=True)

    messages_per_day_vals = stools.get_messages_per_day(msgs).values()

    xticks, xticks_labels, xlabel = _get_xticks(msgs)

    min_day = len(min(messages_per_day_vals, key=lambda day: len(day)))
    max_day = len(max(messages_per_day_vals, key=lambda day: len(day)))
    pal = sns.color_palette("Greens_d", max_day - min_day + 1)[::-1]

    ax = sns.barplot(x=list(range(len(messages_per_day_vals))), y=[len(day) for day in messages_per_day_vals],
                     edgecolor="none", palette=np.array(pal)[[len(day) - min_day for day in messages_per_day_vals]])
    _change_bar_width(ax, 1.)
    ax.set(xlabel=xlabel, ylabel="messages")
    ax.set_xticklabels(xticks_labels)

    ax.tick_params(axis='x', bottom=True, color="#A9A9A9")
    plt.xticks(xticks, rotation=65)

    fig = plt.gcf()
    fig.set_size_inches(20, 10)
    fig.savefig(os.path.join(path_to_save, barplot_messages_per_day.__name__ + ".png"), dpi=600)

    # plt.show()
    log_line(f"{barplot_messages_per_day.__name__} was created.")
    plt.close("all")


def barplot_messages_per_minutes(msgs, path_to_save, minutes=2):
    sns.set(style="whitegrid", palette="muted")
    sns.despine(top=True)

    messages_per_minutes = stools.get_messages_per_minutes(msgs, minutes)

    xticks_labels = stools.get_hours()
    xticks = [i * 60 // minutes for i in range(24)]

    min_minutes = len(min(messages_per_minutes.values(), key=lambda day: len(day)))
    max_minutes = len(max(messages_per_minutes.values(), key=lambda day: len(day)))
    pal = sns.color_palette("GnBu_d", max_minutes - min_minutes + 1)[::-1]

    ax = sns.barplot(x=list(range(len(messages_per_minutes))), y=[len(day) for day in messages_per_minutes.values()],
                     edgecolor="none",
                     palette=np.array(pal)[[len(day) - min_minutes for day in messages_per_minutes.values()]])
    _change_bar_width(ax, 1.)
    ax.set(xlabel="hour", ylabel="messages")
    ax.set_xticklabels(xticks_labels)

    ax.tick_params(axis='x', bottom=True, color="#A9A9A9")
    plt.xticks(xticks, rotation=65)

    fig = plt.gcf()
    fig.set_size_inches(20, 10)

    fig.savefig(os.path.join(path_to_save, barplot_messages_per_minutes.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{barplot_messages_per_minutes.__name__} was created.")
    plt.close("all")


def barplot_words(msgs, your_name, target_name, words, topn, path_to_save):
    sns.set(style="whitegrid")

    your_msgs = [msg for msg in msgs if msg.author == your_name]
    target_msgs = [msg for msg in msgs if msg.author == target_name]

    your_words_cnt = stools.get_words_countered(your_msgs)
    target_words_cnt = stools.get_words_countered(target_msgs)

    words.sort(key=lambda w: your_words_cnt[w] + target_words_cnt[w], reverse=True)
    df_dict = {"name": [], "word": [], "num": []}
    for word in words[:topn]:
        df_dict["word"].extend([word, word])
        df_dict["name"].append(your_name)
        df_dict["num"].append(your_words_cnt[word])
        df_dict["name"].append(target_name)
        df_dict["num"].append(target_words_cnt[word])

    ax = sns.barplot(x="word", y="num", hue="name", data=pd.DataFrame(df_dict), palette="PuBu")
    ax.legend(ncol=1, loc="upper right", frameon=True)
    ax.set(ylabel="messages", xlabel='')

    fig = plt.gcf()
    fig.set_size_inches(14, 8)

    fig.savefig(os.path.join(path_to_save, barplot_words.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{barplot_words.__name__} was created.")
    plt.close("all")


def barplot_emojis(msgs, your_name, target_name, topn, path_to_save):
    sns.set(style="whitegrid")

    mc_emojis = stools.get_emoji_countered(msgs).most_common(topn)
    if not mc_emojis:
        return
    your_msgs = [msg for msg in msgs if msg.author == your_name]
    target_msgs = [msg for msg in msgs if msg.author == target_name]

    your_emojis_cnt = stools.get_emoji_countered(your_msgs)
    target_emojis_cnt = stools.get_emoji_countered(target_msgs)

    df_dict = {"name": [], "emoji": [], "num": []}
    for e, _ in mc_emojis:
        df_dict["emoji"].extend([emoji.demojize(e), emoji.demojize(e)])
        df_dict["name"].append(your_name)
        df_dict["num"].append(your_emojis_cnt[e])
        df_dict["name"].append(target_name)
        df_dict["num"].append(target_emojis_cnt[e])

    ax = sns.barplot(x="num", y="emoji", hue="name", data=pd.DataFrame(df_dict), palette="PuBu")
    ax.set(ylabel="emoji name", xlabel="emojis")
    ax.legend(ncol=1, loc="lower right", frameon=True)

    fig = plt.gcf()
    fig.set_size_inches(11, 8)
    plt.tight_layout()

    fig.savefig(os.path.join(path_to_save, barplot_emojis.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{barplot_emojis.__name__} was created.")
    plt.close("all")


def barplot_messages_per_weekday(msgs, your_name, target_name, path_to_save):
    sns.set(style="whitegrid", palette="pastel")

    messages_per_weekday = stools.get_messages_per_weekday(msgs)
    labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    ax = sns.barplot(x=labels, y=[len(weekday) for weekday in messages_per_weekday.values()],
                     label=your_name, color="b")
    sns.set_color_codes("muted")
    sns.barplot(x=labels,
                y=[len([msg for msg in weekday if msg.author == target_name])
                   for weekday in messages_per_weekday.values()],
                label=target_name, color="b")

    ax.legend(ncol=2, loc="lower right", frameon=True)
    ax.set(ylabel="messages")
    sns.despine(right=True, top=True)

    fig = plt.gcf()
    fig.set_size_inches(11, 8)

    fig.savefig(os.path.join(path_to_save, barplot_messages_per_weekday.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{barplot_messages_per_weekday.__name__} was created.")
    plt.close("all")


def distplot_messages_per_hour(msgs, path_to_save):
    sns.set(style="whitegrid")

    ax = sns.distplot([msg.date.hour for msg in msgs], bins=range(25), color="m", kde=False)
    ax.set_xticklabels(stools.get_hours())
    ax.set(xlabel="hour", ylabel="messages")
    ax.margins(x=0)

    plt.xticks(range(24), rotation=65)
    plt.tight_layout()
    fig = plt.gcf()
    fig.set_size_inches(11, 8)

    fig.savefig(os.path.join(path_to_save, distplot_messages_per_hour.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{distplot_messages_per_hour.__name__} was created.")
    plt.close("all")


def distplot_messages_per_day(msgs, path_to_save):
    sns.set(style="whitegrid")

    data = stools.get_messages_per_day(msgs)

    max_day_len = len(max(data.values(), key=len))
    ax = sns.distplot([len(day) for day in data.values()], bins=list(range(0, max_day_len, 50)) + [max_day_len],
                      color="m", kde=False)
    ax.set(xlabel="messages", ylabel="days")
    ax.margins(x=0)

    fig = plt.gcf()
    fig.set_size_inches(11, 8)

    fig.savefig(os.path.join(path_to_save, distplot_messages_per_day.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{distplot_messages_per_day.__name__} was created.")
    plt.close("all")


def distplot_messages_per_month(msgs, path_to_save):
    sns.set(style="whitegrid")

    start_date = msgs[0].date.date()
    (xticks, xticks_labels, xlabel) = _get_xticks(msgs)

    ax = sns.distplot([(msg.date.date() - start_date).days for msg in msgs],
                      bins=xticks + [(msgs[-1].date.date() - start_date).days], color="m", kde=False)
    ax.set_xticklabels(xticks_labels)
    ax.set(xlabel=xlabel, ylabel="messages")
    ax.margins(x=0)

    plt.xticks(xticks, rotation=65)
    plt.tight_layout()
    fig = plt.gcf()
    fig.set_size_inches(11, 8)

    fig.savefig(os.path.join(path_to_save, distplot_messages_per_month.__name__ + ".png"), dpi=600)
    # plt.show()
    log_line(f"{distplot_messages_per_month.__name__} was created.")
    plt.close("all")


def lineplot_message_length(msgs, your_name, target_name, path_to_save):
    sns.set(style="whitegrid")

    (x, y_total), (xticks, xticks_labels, xlabel) = _get_plot_data(msgs), _get_xticks(msgs)

    y_your = [avg([len(msg.text) for msg in period if msg.author == your_name]) for period in y_total]
    y_target = [avg([len(msg.text) for msg in period if msg.author == target_name]) for period in y_total]

    plt.fill_between(x, y_your, alpha=0.3)
    ax = sns.lineplot(x=x, y=y_your, palette="denim blue", linewidth=2.5, label=your_name)
    plt.fill_between(x, y_target, alpha=0.3)
    sns.lineplot(x=x, y=y_target, linewidth=2.5, label=target_name)

    ax.set(xlabel=xlabel, ylabel="average message length (characters)")
    ax.set_xticklabels(xticks_labels)

    ax.tick_params(axis='x', bottom=True, color="#A9A9A9")
    plt.xticks(xticks, rotation=65)
    ax.margins(x=0, y=0)

    # plt.tight_layout()
    fig = plt.gcf()
    fig.set_size_inches(13, 7)

    fig.savefig(os.path.join(path_to_save, lineplot_message_length.__name__ + ".png"), dpi=600)
    # plt.show()
    plt.close("all")
    log_line(f"{lineplot_message_length.__name__} was created.")


def lineplot_messages(msgs, your_name, target_name, path_to_save):
    sns.set(style="whitegrid")

    (x, y_total), (xticks, xticks_labels, xlabel) = _get_plot_data(msgs), _get_xticks(msgs)

    y_your = [len([msg for msg in period if msg.author == your_name]) for period in y_total]
    y_target = [len([msg for msg in period if msg.author == target_name]) for period in y_total]

    plt.fill_between(x, y_your, alpha=0.3)
    ax = sns.lineplot(x=x, y=y_your, palette="denim blue", linewidth=2.5, label=your_name)
    plt.fill_between(x, y_target, alpha=0.3)
    sns.lineplot(x=x, y=y_target, linewidth=2.5, label=target_name)

    ax.set(xlabel=xlabel, ylabel="messages")
    ax.set_xticklabels(xticks_labels)

    ax.tick_params(axis='x', bottom=True, color="#A9A9A9")
    plt.xticks(xticks, rotation=65)
    ax.margins(x=0, y=0)

    # plt.tight_layout()
    fig = plt.gcf()
    fig.set_size_inches(13, 7)

    fig.savefig(os.path.join(path_to_save, lineplot_messages.__name__ + ".png"), dpi=600)
    # plt.show()
    plt.close("all")
    log_line(f"{lineplot_messages.__name__} was created.")


def wordcloud(msgs, words, path_to_save):
    all_words_list = []
    words_cnt = stools.get_words_countered(msgs)
    # we need to create a huge string which contains each word as many times as it encounters in messages.
    for word in set(words):
        all_words_list.extend([word] * (words_cnt[word]))
    random.shuffle(all_words_list, random.random)  # don't forget to shuffle !
    all_words_string = ' '.join(all_words_list)

    # the cloud will be a circle.
    radius = 500
    x, y = np.ogrid[:2 * radius, :2 * radius]
    mask = (x - radius) ** 2 + (y - radius) ** 2 > radius ** 2
    mask = 255 * mask.astype(int)

    word_cloud = wc.WordCloud(background_color="white", repeat=False, mask=mask)
    word_cloud.generate(all_words_string)

    plt.axis("off")
    plt.imshow(word_cloud, interpolation="bilinear")

    word_cloud.to_file(os.path.join(path_to_save, wordcloud.__name__ + ".png"))
    # plt.show()
    plt.close()
    log_line(f"{wordcloud.__name__} was created.")
