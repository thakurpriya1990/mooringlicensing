from rest_framework import views, viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from mooringlicensing import settings
from mooringlicensing.components.approvals.models import DcvPermit
from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.payments_ml.models import FeeConstructor
from mooringlicensing.components.payments_ml.serializers import DcvPermitSerializer


class GetSeasonsForDcvDict(views.APIView):
    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        # Return current and future seasons for the DCV permit
        application_type = ApplicationType.objects.get(code=settings.APPLICATION_TYPE_DCV_PERMIT['code'])
        fee_constructors = FeeConstructor.get_current_and_future_fee_constructors_by_application_type_and_date(application_type,)
        data = [{'id': item.fee_season.id, 'name': item.fee_season.__str__()} for item in fee_constructors]
        return Response(data)


class DcvPermitViewSet(viewsets.ModelViewSet):
    queryset = DcvPermit.objects.all().order_by('id')
    serializer_class = DcvPermitSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        dcv_permit = serializer.save()

        return Response(serializer.data)
