<template lang="html">
    <div id="current_moorings">
        <FormSection v-if="currentMooringDisplayText" label="Current Moorings" Index="current_mooring">
            <div class="row form-group">
                <div class="col-sm-9">
                    <label for="" class="col-sm-12 control-label">{{ currentMooringDisplayText }}</label>

                        <div class="col-sm-9">
                            <input 
                            @change="resetCurrentMooring" 
                            :disabled="readonly" 
                            type="radio" 
                            id="change_mooring_false" 
                            name="change_mooring_false" 
                            :value="false" 
                            v-model="change_mooring" 
                            required
                            />
                            <label for="change_mooring_false" class="control-label">No</label>
                        </div>
                        <div class="col-sm-9">
                            <input 
                            @change="resetCurrentMooring" 
                            :disabled="readonly" 
                            type="radio" 
                            id="change_mooring_true" 
                            name="change_mooring_true" 
                            :value="true" 
                            v-model="change_mooring" 
                            required
                            />
                            <label for="change_mooring_true" class="control-label">Yes</label>
                        </div>

                </div>
            </div>
        </FormSection>
    </div>

</template>
<script>
import Vue from 'vue'
import FormSection from '@/components/forms/section_toggle.vue'
var select2 = require('select2');
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'

    export default {
        name:'current_mooring',
        data:function () {
            return {
                change_mooring: false,
            }
        },
        components:{
            FormSection,
        },
        props:{
            proposal:{
                type: Object,
                required:true
            },
            readonly:{
                type: Boolean,
                default: true,
            },
            is_internal:{
              type: Boolean,
              default: false
            },
        },
        computed: {
            /*
            mooringLicenceCurrentVesselDisplayText: function() {
                let displayText = '';
                if (this.proposal && this.proposal.mooring_licence_vessels && this.proposal.mooring_licence_vessels.length) {
                    displayText += `Your mooring licence ${this.proposal.approval_lodgement_number} 
                    currently lists the following vessels ${this.proposal.mooring_licence_vessels.toString()}.`;
                }
                return displayText;
            },
            */
            currentMooringDisplayText: function() {
                let displayText = '';
                if (this.proposal && this.proposal.authorised_user_moorings_str) {
                    displayText += `Your ${this.proposal.approval_type_text} ${this.proposal.approval_lodgement_number} 
                    lists moorings ${this.proposal.authorised_user_moorings_str}. Do you want to apply for another mooring to be listed on the Authorised User Permit?`;
                }
                /*
                if (this.proposal && this.proposal.mooring_licence_vessels && this.proposal.mooring_licence_vessels.length) {
                    displayText += `Your Authorised User Permit ${this.proposal.approval_lodgement_number} 
                    lists the following vessel ${this.proposal.mooring_licence_vessels.toString()}.`;
                }
                */
                return displayText;
            },

        },
        methods:{
            resetCurrentMooring: function() {
                this.$nextTick(() => {
                    this.$emit("resetCurrentMooring", this.change_mooring)
                });
            },
        },
        mounted: function () {
        },
        created: function() {
        },
    }
</script>

<style lang="css" scoped>
    input[type=text] {
        padding-left: 1em;
    }
</style>

