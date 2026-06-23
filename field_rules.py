"""Field rules and limits used during trial processing.

These values are kept here so they can be imported only when a processing
function actually needs them.
"""

# Maximum allowed length per tag. Values longer than this are truncated.
TRUNCATE_FIELDS = {
    'hc_freetext': 3000,
    'i_freetext': 3000,
    'inclusion_criteria': 4000,
    'exclusion_criteria': 4000,
    'prim_outcome': 8000,
    'sec_outcome': 8000,
    'results_IPD_description': 2000,
    'address': 250,
    'lastname': 50,
    'agemax': 50,
    'results_summary': 4000,
    'results_outcome_measures': 8000,
    'hc_keyword': 500,
    'firstname': 50,
    'target_size': 255,
    'results_url_link': 255,
    'contact_name': 512,
    'country2': 50,
    'study_design': 1000,
    'i_keyword': 500,

}

# Date tags whose leading/trailing whitespace must be stripped.
DATE_FIELDS_TO_STRIP = [
    'date_registration',
    'results_date_posted',
    'results_date_completed',
    'results_date_first_publication'
]

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
