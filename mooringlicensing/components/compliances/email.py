import logging

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings

from mooringlicensing.components.emails.emails import TemplateEmailBase
from ledger.accounts.models import EmailUser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

SYSTEM_NAME = settings.SYSTEM_NAME_SHORT + ' Automated Message'


class ComplianceExternalSubmitSendNotificationEmail(TemplateEmailBase):
    subject = 'Licence/Permit requirement'
    html_template = 'mooringlicensing/emails/send_external_submit_notification.html'
    txt_template = 'mooringlicensing/emails/send_external_submit_notification.txt'


class ComplianceSubmitSendNotificationEmail(TemplateEmailBase):
    subject = 'A new Compliance has been submitted.'
    html_template = 'mooringlicensing/emails/send_submit_notification.html'
    txt_template = 'mooringlicensing/emails/send_submit_notification.txt'


class ComplianceAcceptNotificationEmail(TemplateEmailBase):
    subject = 'Confirmation - Licence/Permit requirement completed.'
    html_template = 'mooringlicensing/emails/compliance_accept_notification.html'
    txt_template = 'mooringlicensing/emails/compliance_accept_notification.txt'


class ComplianceAmendmentRequestSendNotificationEmail(TemplateEmailBase):
    subject = 'Licence/Permit requirement.'
    html_template = 'mooringlicensing/emails/send_amendment_notification.html'
    txt_template = 'mooringlicensing/emails/send_amendment_notification.txt'


class ComplianceReminderNotificationEmail(TemplateEmailBase):
    subject = 'Licence/Permit requirement overdue.'
    html_template = 'mooringlicensing/emails/send_reminder_notification.html'
    txt_template = 'mooringlicensing/emails/send_reminder_notification.txt'


class ComplianceInternalReminderNotificationEmail(TemplateEmailBase):
    subject = 'A Compliance with requirements has passed the due date.'
    html_template = 'mooringlicensing/emails/send_internal_reminder_notification.html'
    txt_template = 'mooringlicensing/emails/send_internal_reminder_notification.txt'


class ComplianceDueNotificationEmail(TemplateEmailBase):
    subject = 'Licence/Permit requirement due'
    html_template = 'mooringlicensing/emails/send_due_notification.html'
    txt_template = 'mooringlicensing/emails/send_due_notification.txt'


class ComplianceInternalDueNotificationEmail(TemplateEmailBase):
    subject = 'A Compliance with requirements is due for submission.'
    html_template = 'mooringlicensing/emails/send_internal_due_notification.html'
    txt_template = 'mooringlicensing/emails/send_internal_due_notification.txt'


def send_amendment_email_notification(amendment_request, request, compliance, is_test=False):
    email = ComplianceAmendmentRequestSendNotificationEmail()
    #reason = amendment_request.get_reason_display()
    reason = amendment_request.reason.reason
    url = request.build_absolute_uri(reverse('external-compliance-detail',kwargs={'compliance_pk': compliance.id}))
    url = ''.join(url.split('-internal'))
    login_url = request.build_absolute_uri(reverse('external'))
    login_url = ''.join(login_url.split('-internal'))
    context = {
        'compliance': compliance,
        'reason': reason,
        'amendment_request_text': amendment_request.text,
        'url': url
    }

    submitter = compliance.submitter.email if compliance.submitter and compliance.submitter.email else compliance.proposal.submitter.email
    all_ccs = []
    if compliance.proposal.org_applicant and compliance.proposal.org_applicant.email:
        cc_list = compliance.proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]
    msg = email.send(submitter,cc=all_ccs, context=context)
    if is_test:
        return

    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_compliance_email(msg, compliance, sender=sender)
    if compliance.proposal.org_applicant:
        _log_org_email(msg, compliance.proposal.org_applicant, compliance.submitter, sender=sender)
    else:
        _log_user_email(msg, compliance.proposal.submitter, compliance.submitter, sender=sender)


#send reminder emails if Compliance has not been lodged by due date. Used in Cron job so cannot use 'request' parameter
def send_reminder_email_notification(compliance, is_test=False):
    """ Used by the management command, therefore have no request object - therefore explicitly defining base_url """
    email = ComplianceReminderNotificationEmail()
    url=settings.SITE_URL if settings.SITE_URL else ''
    url+=reverse('external-compliance-detail',kwargs={'compliance_pk': compliance.id})
    login_url=settings.SITE_URL if settings.SITE_URL else ''
    login_url+=reverse('external')
    context = {
        'compliance': compliance,
        'url': url,
        'login_url': login_url
    }

    submitter = compliance.submitter.email if compliance.submitter and compliance.submitter.email else compliance.proposal.submitter.email
    all_ccs = []
    if compliance.proposal.org_applicant and compliance.proposal.org_applicant.email:
        cc_list = compliance.proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]
    msg = email.send(submitter, cc=all_ccs, context=context)
    if is_test:
        return

    sender = settings.DEFAULT_FROM_EMAIL
    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        sender_user = EmailUser.objects.create(email=sender, password='', is_staff=True)
    _log_compliance_email(msg, compliance, sender=sender_user)
    if compliance.proposal.org_applicant:
        _log_org_email(msg, compliance.proposal.org_applicant, compliance.submitter, sender=sender_user)
    else:
        _log_user_email(msg, compliance.proposal.submitter, compliance.submitter, sender=sender)


def send_internal_reminder_email_notification(compliance, is_test=False):
    from mooringlicensing.components.emails.utils import make_url_for_internal
    email = ComplianceInternalReminderNotificationEmail()
    url = settings.SITE_URL
    url += reverse('internal-compliance-detail', kwargs={'compliance_pk': compliance.id})
    url = make_url_for_internal(url)

    context = {
        'compliance': compliance,
        'url': url
    }

    msg = email.send(compliance.proposal.assessor_recipients, context=context)
    if is_test:
        return

    sender = settings.DEFAULT_FROM_EMAIL
    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        sender_user = EmailUser.objects.create(email=sender, password='')
    _log_compliance_email(msg, compliance, sender=sender_user)
    if compliance.proposal.org_applicant:
        _log_org_email(msg, compliance.proposal.org_applicant, compliance.submitter, sender=sender_user)
    else:
        _log_user_email(msg, compliance.proposal.submitter, compliance.submitter, sender=sender)


def send_due_email_notification(compliance, is_test=False):
    email = ComplianceDueNotificationEmail()
    url=settings.SITE_URL
    url+=reverse('external-compliance-detail',kwargs={'compliance_pk': compliance.id})
    context = {
        'compliance': compliance,
        'url': url
    }

    submitter = compliance.submitter.email if compliance.submitter and compliance.submitter.email else compliance.proposal.submitter.email
    all_ccs = []
    if compliance.proposal.org_applicant and compliance.proposal.org_applicant.email:
        cc_list = compliance.proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]
    msg = email.send(submitter,cc=all_ccs, context=context)
    if is_test:
        return

    sender = settings.DEFAULT_FROM_EMAIL
    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        sender_user = EmailUser.objects.create(email=sender, password='', is_staff=True)
    _log_compliance_email(msg, compliance, sender=sender_user)
    if compliance.proposal.org_applicant:
        _log_org_email(msg, compliance.proposal.org_applicant, compliance.submitter, sender=sender_user)
    else:
        _log_user_email(msg, compliance.proposal.submitter, compliance.submitter, sender=sender)


def send_internal_due_email_notification(compliance, is_test=False):
    from mooringlicensing.components.emails.utils import make_url_for_internal

    email = ComplianceInternalDueNotificationEmail()
    url = settings.SITE_URL
    url += reverse('internal-compliance-detail', kwargs={'compliance_pk': compliance.id})
    url = make_url_for_internal(url)

    context = {
        'compliance': compliance,
        'url': url
    }

    msg = email.send(compliance.proposal.assessor_recipients, context=context)
    if is_test:
        return

    sender = settings.DEFAULT_FROM_EMAIL
    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        sender_user = EmailUser.objects.create(email=sender, password='', is_staff=True)
    _log_compliance_email(msg, compliance, sender=sender_user)
    if compliance.proposal.org_applicant:
        _log_org_email(msg, compliance.proposal.org_applicant, compliance.submitter, sender=sender_user)
    else:
        _log_user_email(msg, compliance.proposal.submitter, compliance.submitter, sender=sender)


def send_compliance_accept_email_notification(compliance,request, is_test=False):
    email = ComplianceAcceptNotificationEmail()

    context = {
        'compliance': compliance
    }
    submitter = compliance.submitter.email if compliance.submitter and compliance.submitter.email else compliance.proposal.submitter.email
    all_ccs = []
    if compliance.proposal.org_applicant and compliance.proposal.org_applicant.email:
        cc_list = compliance.proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]
    msg = email.send(submitter, cc=all_ccs, context=context)
    if is_test:
        return

    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_compliance_email(msg, compliance, sender=sender)
    if compliance.proposal.org_applicant:
        _log_org_email(msg, compliance.proposal.org_applicant, compliance.submitter, sender=sender)
    else:
        _log_user_email(msg, compliance.proposal.submitter, compliance.submitter, sender=sender)


def send_external_submit_email_notification(request, compliance, is_test=False):
    email = ComplianceExternalSubmitSendNotificationEmail()
    url = request.build_absolute_uri(reverse('external-compliance-detail',kwargs={'compliance_pk': compliance.id}))
    url = ''.join(url.split('-internal'))
    submitter = compliance.submitter if compliance.submitter and compliance.submitter.email else compliance.proposal.submitter
    context = {
        'compliance': compliance,
        'submitter': submitter.get_full_name(),
        'url': url
    }
    all_ccs = []
    if compliance.proposal.org_applicant and compliance.proposal.org_applicant.email:
        cc_list = compliance.proposal.org_applicant.email
        if cc_list:
            all_ccs = [cc_list]
    msg = email.send(submitter.email,cc=all_ccs, context=context)
    if is_test:
        return

    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_compliance_email(msg, compliance, sender=sender)
    if compliance.proposal.org_applicant:
        _log_org_email(msg, compliance.proposal.org_applicant, compliance.submitter, sender=sender)
    else:
        _log_user_email(msg, compliance.proposal.submitter, compliance.submitter, sender=sender)


def send_submit_email_notification(request, compliance, is_test=False):
    from mooringlicensing.components.emails.utils import make_url_for_internal

    email = ComplianceSubmitSendNotificationEmail()
    url = request.build_absolute_uri(reverse('internal-compliance-detail', kwargs={'compliance_pk': compliance.id}))
    url = make_url_for_internal(url)

    context = {
        'compliance': compliance,
        'url': url
    }

    msg = email.send(compliance.proposal.assessor_recipients, context=context)
    if is_test:
        return

    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    _log_compliance_email(msg, compliance, sender=sender)
    if compliance.proposal.org_applicant:
        _log_org_email(msg, compliance.proposal.org_applicant, compliance.submitter, sender=sender)
    else:
        _log_user_email(msg, compliance.proposal.submitter, compliance.submitter, sender=sender)


def _log_compliance_email(email_message, compliance, sender=None):
    from mooringlicensing.components.compliances.models import ComplianceLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = compliance.submitter.email
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = compliance.submitter

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'compliance': compliance,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = ComplianceLogEntry.objects.create(**kwargs)

    return email_entry


def _log_org_email(email_message, organisation, customer ,sender=None):
    from mooringlicensing.components.organisations.models import OrganisationLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = customer.email
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = customer

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'organisation': organisation,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = OrganisationLogEntry.objects.create(**kwargs)

    return email_entry


def _log_user_email(email_message, target_email_user, customer, sender=None, attachments=[]):
    from ledger.accounts.models import EmailUserLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = customer
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = customer

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'emailuser': target_email_user,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = EmailUserLogEntry.objects.create(**kwargs)

    for attachment in attachments:
        path_to_file = '{}/emailuser/{}/communications/{}'.format(settings.MEDIA_APP_DIR, target_email_user.id, attachment[0])
        path = default_storage.save(path_to_file, ContentFile(attachment[1]))
        email_entry.documents.get_or_create(_file=path_to_file, name=attachment[0])

    return email_entry
