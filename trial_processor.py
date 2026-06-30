"""Trial pre-processing transformations applied before XSD validation.

Each function mutates the given <trial> element in place and appends any
generated warning messages to the provided ``trial_warnings`` list.
"""

from lxml import etree


def truncate_fields(trial, trial_warnings):
    """Trunca os campos que ultrapassam o tamanho máximo permitido.

    Para cada tag listada em TRUNCATE_FIELDS, se o texto for maior que o limite,
    corta o conteúdo e acrescenta '...', registrando um aviso. O import é feito
    aqui dentro para só carregar a tabela de limites quando esta função roda.
    """
    from field_rules import TRUNCATE_FIELDS

    for tag, max_len in TRUNCATE_FIELDS.items():
        for element in trial.findall(f".//{tag}"):
            if element is not None and element.text and len(element.text) > max_len:
                # Define o ponto de corte. Ex: Se limite é 50, corta em 45 para sobrar espaço pros '...'
                cut_point = 45 if max_len == 50 else (max_len - 3)

                # Efetua o corte e adiciona os 3 pontinhos
                element.text = element.text[:cut_point] + "..."

                trial_warnings.append(f"Warning: The &lt;{tag}&gt; tag exceeded the allowed limit. It will be truncated at {cut_point} characters...")


def split_multiple_countries(trial, trial_warnings):
    """Separa múltiplos países enviados dentro de uma única tag <country2>.

    --- Correção de múltiplos países (Ex: Sri Lanka) ---
    Quando uma <country2> traz vários países juntos, cria uma tag por país
    (cada um limitado a 50 caracteres) e remove a tag original, gerando um aviso.
    """
    countries_node = trial.find('.//countries')
    if countries_node is not None:
        for country_elem in countries_node.findall('country2'):
            if country_elem.text and ',' in country_elem.text:
                country_list = [c.strip() for c in country_elem.text.split(';') if c.strip()]

                if len(country_list) > 1:
                    for c_name in country_list:
                        new_c = etree.Element('country2')
                        new_c.text = c_name[:50]
                        country_elem.addprevious(new_c)

                    countries_node.remove(country_elem)
                    trial_warnings.append("Warning: Multiple countries sent in a single &lt;country2&gt; tag. They will be separated automatically. Correct behavior: use a separate tag for each country.")


def strip_date_whitespace(trial, trial_warnings):
    """Remove espaços em branco no início/fim dos campos de data.

    Percorre as tags de data (DATE_FIELDS_TO_STRIP); se houver espaços sobrando,
    aplica strip() e registra um aviso pedindo correção na fonte.
    """
    from field_rules import DATE_FIELDS_TO_STRIP

    for date_tag in DATE_FIELDS_TO_STRIP:
        date_node = trial.find(f'.//{date_tag}')
        if date_node is not None and date_node.text:
            stripped_date = date_node.text.strip()
            if date_node.text != stripped_date:
                date_node.text = stripped_date
                trial_warnings.append(f"Warning: The &lt;{date_tag}&gt; tag contained leading or trailing whitespace. The spaces were automatically ignored for import, but please correct the formatting in your source file.")


def fill_empty_containers(trial, trial_warnings):
    """Preenche tags-container vazias com uma estrutura padrão '-' para o XSD.

    Detecta dois casos de container vazio (mãe totalmente vazia ou com uma única
    subtag vazia) e, conforme a regra em EMPTY_CONTAINERS_RULES, injeta a subtag
    obrigatória preenchida com '-'. Trata estruturas mais complexas
    (secondary_id e ethics_review) montando seus subelementos, e gera um aviso.
    """
    from field_rules import EMPTY_CONTAINERS_RULES

    for parent_tag, child_tag in EMPTY_CONTAINERS_RULES.items():
        parent_node = trial.find(f'.//{parent_tag}')
        if parent_node is not None:
            total_children = len(parent_node)

            # 1. Caso clássico: A tag mãe está totalmente vazia (<tag/> ou <tag></tag>)
            is_empty_parent = (parent_node.text is None or not parent_node.text.strip()) and total_children == 0

            # 2. Caso específico: A tag mãe tem UMA tag filha, mas essa subtag está vazia (ex: <intervention_code><i_code/></intervention_code>)
            is_subtag_empty = False
            if total_children == 1:
                child_node = parent_node.find(f'./{child_tag}')
                if child_node is not None and (child_node.text is None or not child_node.text.strip()) and len(child_node) == 0:
                    is_subtag_empty = True

            # Se cair em qualquer um dos dois casos de falso positivo por estar vazio
            if is_empty_parent or is_subtag_empty:
                # Limpa qualquer estrutura mal formada que sobrou dentro dela
                parent_node.clear()

                # Se for uma tag com estrutura interna mais complexa (como secondary_id ou ethics_review)
                # criamos o nó da subtag respeitando o XSD, mas preenchendo os dados obrigatórios com "-"
                if child_tag == 'secondary_id':
                    new_child = etree.Element(child_tag)
                    sec_id = etree.Element('sec_id')
                    sec_id.text = "-"
                    authority = etree.Element('issuing_authority')
                    authority.text = "-"
                    new_child.append(sec_id)
                    new_child.append(authority)
                elif child_tag == 'ethics_review':
                    new_child = etree.Element(child_tag)
                    for sub_elem in ['status', 'approval_date', 'contact_name', 'contact_address', 'contact_phone', 'contact_email']:
                        elem = etree.Element(sub_elem)
                        elem.text = "-"
                        new_child.append(elem)
                else:
                    # Para as tags simples (hc_code, hc_keyword, i_code, i_keyword, sponsor_name)
                    new_child = etree.Element(child_tag)
                    new_child.text = "-"

                # Insere o filho válido na tag principal para o XSD ficar feliz e manter a ordem
                parent_node.append(new_child)

                trial_warnings.append(f"Warning: The container &lt;{parent_tag}&gt; or its subtag was empty. Automatically filled with standard structure '-' to comply with the schema sequence.")


def check_empty_fields(trial):
    """Aplica a política de campos vazios (EMPTY_FIELD_POLICY) ao trial.

    Um campo é considerado VAZIO em qualquer um destes três casos:
      1. <tag> </tag>  -> presente, mas só com espaços/sem texto;
      2. <tag/>        -> presente, mas autofechada;
      3. ausente        -> a tag nem aparece no XML do trial.

    Para cada campo vazio, decide o comportamento conforme a política:
      - 'error'   -> adiciona à lista de erros (campo importante vazio);
      - 'warning' -> adiciona à lista de avisos (vazio, mas não obrigatório);
      - 'nothing' -> ignora (pode vir vazio sem problema).

    Retorna uma tupla (errors, warnings), onde 'errors' é uma lista de
    (linha, mensagem) e 'warnings' é uma lista de mensagens.
    """
    from field_rules import EMPTY_FIELD_POLICY

    errors = []
    warnings = []

    def flag(tag, policy, line):
        """Registra a mensagem de erro ou aviso para um campo vazio."""
        if policy == 'error':
            errors.append((
                line,
                f"Empty Required Field: The tag &lt;{tag}&gt; is empty but is required. "
                f"[TIP: Fill in the &lt;{tag}&gt; field.]"
            ))
        elif policy == 'warning':
            warnings.append(
                f"Warning: The &lt;{tag}&gt; tag is empty. "
                f"It is recommended to fill it in, but it is not mandatory."
            )

    for tag, policy in EMPTY_FIELD_POLICY.items():
        # 'nothing' não gera nenhuma mensagem, então nem precisa procurar a tag.
        if policy == 'nothing':
            continue

        elements = trial.findall(f".//{tag}")

        # Caso 3: a tag não existe no XML -> tratada como vazia.
        if not elements:
            flag(tag, policy, None)
            continue

        # Casos 1 e 2: a tag existe, mas pode estar sem conteúdo.
        for element in elements:
            # Considera vazio: sem texto (ou só espaços) e sem filhos.
            is_empty = (element.text is None or not element.text.strip()) and len(element) == 0
            if is_empty:
                flag(tag, policy, element.sourceline)

    return errors, warnings


def preprocess_trial(trial):
    """Aplica todas as correções no trial (in-place) e devolve a lista de avisos.

    Executa, nesta ordem: truncagem de campos, separação de países, limpeza de
    espaços em datas e preenchimento de containers vazios.
    """
    trial_warnings = []
    truncate_fields(trial, trial_warnings)
    split_multiple_countries(trial, trial_warnings)
    strip_date_whitespace(trial, trial_warnings)
    fill_empty_containers(trial, trial_warnings)
    return trial_warnings
