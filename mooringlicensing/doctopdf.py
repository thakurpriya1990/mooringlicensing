import os
from io import BytesIO

from django.conf import settings
from docxtpl import DocxTemplate
from mooringlicensing.components.main.models import GlobalSettings


def create_apiary_licence_pdf_contents(dcv_permit):
    #import ipdb; ipdb.set_trace()
    # print ("Letter File")
    # confirmation_doc = None
    # if booking.annual_booking_period_group.letter:
    #     print (booking.annual_booking_period_group.letter.path)
    #     confirmation_doc = booking.annual_booking_period_group.letter.path
    # confirmation_doc = settings.BASE_DIR+"/mooring/templates/doc/AnnualAdmissionStickerLetter.docx"

    licence_template = GlobalSettings.objects.get(key=GlobalSettings.KEY_DCV_PERMIT_TEMPLATE_FILE)

    if licence_template._file:
        path_to_template = licence_template._file.path
    else:
        # Use default template file
        path_to_template = os.path.join(settings.BASE_DIR, 'disturbance', 'static', 'disturbance', 'apiary_authority_template.docx')

    doc = DocxTemplate(path_to_template)
    # address = ''
    # if len(booking.details.get('postal_address_line_2', '')) > 0:
    #     address = '{}, {}'.format(booking.details.get('postal_address_line_1', ''),
    #                               booking.details.get('postal_address_line_2', ''))
    # else:
    #     address = '{}'.format(booking.details.get('postal_address_line_1', ''))
    # bookingdate = booking.created + timedelta(hours=8)
    # todaydate = datetime.utcnow() + timedelta(hours=8)
    # stickercreated = ''
    # if booking.sticker_created:
    #     sc = booking.sticker_created + timedelta(hours=8)
    #     stickercreated = sc.strftime('%d %B %Y')
    serializer_context = {
            'dcv_permit': dcv_permit,
            }
    # context_obj = ApprovalSerializerForLicenceDoc(approval, context=serializer_context)
    # context = context_obj.data
    # doc.render(context)
    doc.render({})

    temp_directory = settings.BASE_DIR + "/tmp/"
    try:
        os.stat(temp_directory)
    except:
        os.mkdir(temp_directory)

    f_name = temp_directory + 'dcv_permit_' + str(dcv_permit.id)
    new_doc_file = f_name + '.docx'
    new_pdf_file = f_name + '.pdf'
    doc.save(new_doc_file)
    os.system("libreoffice --headless --convert-to pdf " + new_doc_file + " --outdir " + temp_directory)

    file_contents = None
    with open(new_pdf_file, 'rb') as f:
        file_contents = f.read()
    os.remove(new_doc_file)
    os.remove(new_pdf_file)
    return file_contents
