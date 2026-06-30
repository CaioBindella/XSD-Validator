"""Field rules and limits used during trial processing.

These values are kept here so they can be imported only when a processing
function actually needs them.
"""

# Maximum allowed length per tag. Values longer than this are truncated.
#
# Inclui TODOS os campos obrigatórios do who_ictrp.xsd, com o tamanho máximo
# definido no próprio XSD. A ideia é truncar (e emitir um WARNING) em vez de
# deixar a validação estourar com erro, já que a base aceita salvar valores
# maiores que o recomendado. Campos opcionais que já truncávamos também
# permanecem aqui. Valores customizados pré-existentes (ex.: address=250) são
# mantidos de propósito.
TRUNCATE_FIELDS = {
    # --- main ---
    'trial_id': 255,
    'reg_name': 50,
    'date_registration': 13,
    'primary_sponsor': 2000,
    'public_title': 2000,
    'scientific_title': 2000,
    'date_enrolment': 10,
    'type_enrolment': 50,
    'target_size': 255,
    'recruitment_status': 255,
    'study_type': 255,
    'study_design': 1000,
    'phase': 255,
    'hc_freetext': 3000,            # opcional no XSD, mantido
    'i_freetext': 3000,             # opcional no XSD, mantido
    'results_actual_enrolment': 255,
    'results_date_completed': 13,
    'results_url_link': 255,
    'results_summary': 4000,
    'results_date_posted': 13,
    'results_date_first_publication': 13,
    'results_baseline_char': 8000,
    'results_participant_flow': 8000,
    'results_adverse_events': 8000,
    'results_outcome_measures': 8000,
    'results_url_protocol': 255,
    'results_IPD_plan': 255,
    'results_IPD_description': 2000,

    # --- contacts/contact ---
    'type': 50,
    'firstname': 50,
    'middlename': 50,
    'lastname': 50,
    'address': 255,
    'city': 50,
    'country1': 50,
    'zip': 50,
    'telephone': 255,
    'email': 255,
    'affiliation': 255,

    # --- countries ---
    'country2': 50,

    # --- criteria ---
    'inclusion_criteria': 4000,
    'agemin': 50,
    'agemax': 50,
    'gender': 50,
    'exclusion_criteria': 4000,

    # --- health_condition_code / keyword ---
    'hc_code': 255,
    'hc_keyword': 500,

    # --- intervention_code / keyword ---
    'i_code': 255,
    'i_keyword': 500,

    # --- primary / secondary outcome ---
    'prim_outcome': 8000,
    'sec_outcome': 8000,

    # --- source_support ---
    'source_name': 1000,

    # --- ethics_reviews/ethics_review ---
    'status': 255,
    'approval_date': 10,
    'contact_name': 512,
    'contact_address': 1000,
    'contact_phone': 255,
    'contact_email': 255,
}

# Date tags whose leading/trailing whitespace must be stripped.
DATE_FIELDS_TO_STRIP = [
    'date_registration',
    'results_date_posted',
    'results_date_completed',
    'results_date_first_publication'
]

# =========================================================================
# Política de campos vazios.
#
# Lista TODOS os campos (tags folha) do who_ictrp.xsd. Para cada campo,
# defina o comportamento que o validador deve ter QUANDO o campo estiver
# VAZIO (presente no XML, porém sem conteúdo):
#
#   'error'   -> campo importante: se vier vazio, exibe ERRO para o usuário.
#   'warning' -> campo vazio não faz falta crítica: exibe apenas um AVISO.
#   'nothing' -> pode vir vazio sem problema: não exibe nada.
#
# Basta trocar o valor à frente de cada campo para ajustar o comportamento.
# =========================================================================
EMPTY_FIELD_POLICY = {
    # --- main ---
    'trial_id': 'error',
    'utrn': 'nothing',
    'reg_name': 'error',
    'date_registration': 'error',
    'primary_sponsor': 'warning',
    'public_title': 'warning',
    'acronym': 'nothing',
    'scientific_title': 'warning',
    'scientific_acronym': 'nothing',
    'date_enrolment': 'warning',
    'type_enrolment': 'warning',
    'target_size': 'warning',
    'recruitment_status': 'error',
    'url': 'error',
    'study_type': 'warning',
    'study_design': 'warning',
    'phase': 'nothing',
    'hc_freetext': 'warning',
    'i_freetext': 'warning',
    'results_actual_enrolment': 'nothing',
    'results_date_completed': 'nothing',
    'results_url_link': 'nothing',
    'results_summary': 'nothing',
    'results_date_posted': 'nothing',
    'results_date_first_publication': 'nothing',
    'results_baseline_char': 'nothing',
    'results_participant_flow': 'nothing',
    'results_adverse_events': 'nothing',
    'results_outcome_measures': 'nothing',
    'results_url_protocol': 'nothing',
    'results_IPD_plan': 'nothing',
    'results_IPD_description': 'nothing',

    # --- contacts/contact ---
    'type': 'error',
    'firstname': 'nothing',
    'middlename': 'nothing',
    'lastname': 'nothing',
    'address': 'nothing',
    'city': 'nothing',
    'country1': 'warning',
    'zip': 'nothing',
    'telephone': 'warning',
    'email': 'warning',
    'affiliation': 'nothing',

    # --- countries ---
    'country2': 'warning',

    # --- criteria ---
    'inclusion_criteria': 'warning',
    'agemin': 'nothing',
    'agemax': 'nothing',
    'gender': 'nothing',
    'exclusion_criteria': 'nothing',

    # --- health_condition_code / keyword ---
    'hc_code': 'nothing',
    'hc_keyword': 'nothing',

    # --- intervention_code / keyword ---
    'i_code': 'nothing',
    'i_keyword': 'nothing',

    # --- primary / secondary outcome ---
    'prim_outcome': 'error',
    'sec_outcome': 'warning',

    # --- secondary_sponsor ---
    'sponsor_name': 'nothing',

    # --- secondary_ids/secondary_id ---
    'sec_id': 'nothing',
    'issuing_authority': 'nothing',

    # --- source_support ---
    'source_name': 'nothing',

    # --- ethics_reviews/ethics_review ---
    'status': 'nothing',
    'approval_date': 'nothing',
    'contact_name': 'nothing',
    'contact_address': 'nothing',
    'contact_phone': 'nothing',
    'contact_email': 'nothing',
}

# Mapping of which child tag to inject when the corresponding parent tag is empty.
EMPTY_CONTAINERS_RULES = {
    'health_condition_code': 'hc_code',
    'health_condition_keyword': 'hc_keyword',
    'intervention_code': 'i_code',
    'intervention_keyword': 'i_keyword',
    'primary_outcome': 'prim_outcome',
    'secondary_outcome': 'sec_outcome',
    'secondary_sponsor': 'sponsor_name',
    'secondary_ids': 'secondary_id',
    'source_support': 'source_name',
    'ethics_reviews': 'ethics_review'
}
