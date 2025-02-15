from django.conf import settings
from ledger.accounts.models import EmailUser,Address, Profile,EmailIdentity, EmailUserAction, EmailUserLogEntry, CommunicationsLogEntry

from mooringlicensing.components.main.serializers import CommunicationLogEntrySerializer
from mooringlicensing.components.organisations.models import (
                                    Organisation,
                                )
from mooringlicensing.components.main.models import UserSystemSettings, Document#, ApplicationType
from mooringlicensing.components.proposals.models import Proposal
from mooringlicensing.components.organisations.utils import can_admin_org, is_consultant
from mooringlicensing.helpers import is_mooringlicensing_admin 
from rest_framework import serializers
from ledger.accounts.utils import in_dbca_domain
from ledger.payments.helpers import is_payment_admin

class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ('id','description','file','name','uploaded_date')

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id',
            'line1',
            'locality',
            'state',
            'country',
            'postcode'
        )

class UserSystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSystemSettings
        fields = (
            'one_row_per_park',
        )

class UserOrganisationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='organisation.name')
    abn = serializers.CharField(source='organisation.abn')
    email = serializers.SerializerMethodField()
    is_consultant = serializers.SerializerMethodField(read_only=True)
    is_admin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Organisation
        fields = (
            'id',
            'name',
            'abn',
            'email',
            'is_consultant',
            'is_admin',
        )

    def get_is_admin(self, obj):
        user = EmailUser.objects.get(id=self.context.get('user_id'))
        return can_admin_org(obj, user)

    def get_is_consultant(self, obj):
        user = EmailUser.objects.get(id=self.context.get('user_id'))
        return is_consultant(obj, user)

    def get_email(self, obj):
        email = EmailUser.objects.get(id=self.context.get('user_id')).email
        return email


class UserFilterSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'email',
            'name'
        )

    def get_name(self, obj):
        return obj.get_full_name()


class UserSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    postal_address = serializers.SerializerMethodField()
    personal_details = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()
    contact_details = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_department_user = serializers.SerializerMethodField()
    is_payment_admin = serializers.SerializerMethodField()
    system_settings= serializers.SerializerMethodField()
    is_payment_admin = serializers.SerializerMethodField()
    is_mooringlicensing_admin = serializers.SerializerMethodField()
    readonly_first_name = serializers.SerializerMethodField()
    readonly_last_name = serializers.SerializerMethodField()
    readonly_email = serializers.SerializerMethodField()
    readonly_dob = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'email',
            'residential_address',
            'postal_address',
            'phone_number',
            'mobile_number',
            'personal_details',
            'address_details',
            'contact_details',
            'full_name',
            'is_department_user',
            'is_payment_admin',
            'is_staff',
            'system_settings',
            'is_mooringlicensing_admin',
            'postal_same_as_residential',
            'readonly_first_name',
            'readonly_last_name',
            'readonly_email',
            'dob',
            'readonly_dob',
        )

    def get_readonly_dob(self, obj):
        return True if obj.dob else False

    def get_readonly_first_name(self, obj):
        return True if obj.first_name else False

    def get_readonly_last_name(self, obj):
        return True if obj.last_name else False

    def get_readonly_email(self, obj):
        return True if obj.email else False

    def get_postal_address(self, obj):
        address = {}
        if obj.postal_address:
            address = UserAddressSerializer(obj.postal_address).data
        return address

    def get_personal_details(self,obj):
        return True if obj.last_name  and obj.first_name else False

    def get_address_details(self,obj):
        return True if obj.residential_address else False

    def get_contact_details(self,obj):
        if obj.mobile_number and obj.email:
            return True
        elif obj.phone_number and obj.email:
            return True
        elif obj.mobile_number and obj.phone_number:
            return True
        else:
            return False

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_is_department_user(self, obj):
        if obj.email:
            return in_dbca_domain(obj)
        else:
            return False

    def get_is_payment_admin(self, obj):
        return is_payment_admin(obj)

    def get_system_settings(self, obj):
        try:
            user_system_settings = obj.system_settings.first()
            serialized_settings = UserSystemSettingsSerializer(
                user_system_settings).data
            return serialized_settings
        except:
            return None

    def get_is_mooringlicensing_admin(self, obj):
        request = self.context['request'] if self.context else None
        if request:
            return is_mooringlicensing_admin(request)
        return False


class PersonalSerializer(serializers.ModelSerializer):
    dob = serializers.DateField(format="%d/%m/%Y",input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'dob',
        )

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = (
            'id',
            'email',
            'phone_number',
            'mobile_number',
        )

    def validate(self, obj):
        #Mobile and phone number for dbca user are updated from active directory so need to skip these users from validation.
        domain=None
        if obj['email']:
            domain = obj['email'].split('@')[1]
        if domain in settings.DEPT_DOMAINS:
            return obj
        else:
            if not obj.get('phone_number') and not obj.get('mobile_number'):
                raise serializers.ValidationError('You must provide a mobile/phone number')
        return obj

class EmailUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = EmailUserAction
        fields = '__all__'

# class EmailUserCommsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EmailUserLogEntry
#         fields = '__all__'

class EmailUserCommsSerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()
    type = serializers.CharField(source='log_type')

    class Meta:
        model = EmailUserLogEntry
        # fields = '__all__'
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'type',
            'reference',
            'subject',
            'text',
            'created',
            'staff',
            'emailuser',
            'documents',
        )
        read_only_fields = (
            'customer',
        )

class CommunicationLogEntrySerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=EmailUser.objects.all(),required=False)
    documents = serializers.SerializerMethodField()
    class Meta:
        model = CommunicationsLogEntry
        fields = (
            'id',
            'customer',
            'to',
            'fromm',
            'cc',
            'log_type',
            'reference',
            'subject'
            'text',
            'created',
            'staff',
            'emailuser',
            'documents'
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]

class EmailUserLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()
    class Meta:
        model = EmailUserLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self,obj):
        return [[d.name,d._file.url] for d in obj.documents.all()]
