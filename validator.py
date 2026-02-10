from lxml import etree

def validate_trial_element(trial_element, schema):
    """
    Validates a single <trial> element against the provided XSD schema.
    
    Args:
        trial_element (etree.Element): The specific trial element to validate.
        schema (etree.XMLSchema): The compiled XSD schema.

    Returns:
        tuple: (is_valid (bool), xml_tree (ElementTree), error_log (list))
    """
    # Create a temporary root <trials> to wrap the single <trial>
    # This ensures the structure matches the XSD expectation (root -> trial)
    root = etree.Element("trials")
    root.append(trial_element)
    
    # Create the ElementTree
    doc_tree = etree.ElementTree(root)
    
    # Validate
    is_valid = schema.validate(doc_tree)
    
    return is_valid, doc_tree, schema.error_log