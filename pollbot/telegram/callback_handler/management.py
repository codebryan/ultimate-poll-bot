"""Callback functions needed during creation of a Poll."""
from datetime import datetime

from pollbot.i18n import i18n
from pollbot.helper import poll_required
from pollbot.helper.update import remove_poll_messages, update_poll_messages
from pollbot.display import get_poll_text
from pollbot.telegram.keyboard import get_management_keyboard


@poll_required
def delete_poll(session, context, poll):
    """Permanently delete the poll."""
    remove_poll_messages(session, context.bot, poll)
    session.delete(poll)
    session.commit()
    context.query.answer(i18n.t('callback.deleted', locale=poll.user.locale))


@poll_required
def close_poll(session, context, poll):
    """Close this poll."""
    poll.closed = True
    session.commit()
    update_poll_messages(session, context.bot, poll)
    context.query.answer(i18n.t('callback.closed', locale=poll.user.locale))


@poll_required
def reopen_poll(session, context, poll):
    """Reopen this poll."""
    if not poll.results_visible:
        context.query.answer(i18n.t('callback.cannot_reopen', locale=poll.user.locale))
        return
    poll.closed = False
    if poll.due_date is not None and poll.due_date <= datetime.now():
        poll.due_date = None
        poll.next_notification = None
    session.commit()
    update_poll_messages(session, context.bot, poll)


@poll_required
def reset_poll(session, context, poll):
    """Reset this poll."""
    for vote in poll.votes:
        session.delete(vote)
    session.commit()
    update_poll_messages(session, context.bot, poll)
    context.query.answer(i18n.t('callback.votes_removed', locale=poll.user.locale))


@poll_required
def clone_poll(session, context, poll):
    """Clone this poll."""
    new_poll = poll.clone(session)
    session.commit()

    context.tg_chat.send_message(
            get_poll_text(session, new_poll),
            parse_mode='markdown',
            reply_markup=get_management_keyboard(new_poll),
            disable_web_page_preview=True,
        )
    context.query.answer(i18n.t('callback.cloned', locale=poll.user.locale))
