"""Classificador de subárea por dicionário de termos (palavras-chave ponderadas).

Cada termo tem peso 2 (característico da subárea) ou 1 (genérico). A pontuação de uma subárea é a
soma dos pesos dos termos encontrados no texto (enunciado + alternativas), comparando sem acento, em
minúsculas e com limites de palavra. Termos de peso 1 contam só uma vez por questão. A questão vai para a subárea de maior pontuação se
houver ao menos um termo de peso 2 dessa subárea e:
  - pontuação >= 3; ou
  - a questão está numa seção de TI da prova e pontuação >= 2.
Caso contrário, é considerada fora de computação.
"""
import re

from comum import norm

SUBAREAS = {
    "engenharia_de_software_e_programacao": {
        2: ["java", "python", "javascript", "typescript", "c#", "php", "kotlin", "golang", "linguagem de programacao",
            "orientacao a objetos", "orientada a objetos", "heranca", "polimorfismo", "encapsulamento", "classe abstrata",
            "interface funcional", "padrao de projeto", "padroes de projeto", "design pattern", "singleton", "factory",
            "observer", "decorator", "strategy", "mvc", "solid", "clean code", "refatoracao", "teste unitario",
            "testes unitarios", "tdd", "bdd", "teste de integracao", "testes automatizados", "scrum", "kanban", "sprint",
            "product owner", "xp", "extreme programming", "metodologia agil", "metodos ageis", "desenvolvimento agil",
            "agil", "ageis", "requisitos funcionais", "requisitos nao funcionais", "engenharia de requisitos", "uml",
            "diagrama de classes", "diagrama de sequencia", "caso de uso", "casos de uso", "algoritmo", "algoritmos",
            "complexidade", "recursao", "recursiva", "pilha", "fila", "arvore binaria", "lista encadeada", "ordenacao",
            "bubble sort", "quicksort", "merge sort", "busca binaria", "grafo", "hash", "estrutura de dados", "html",
            "css", "react", "angular", "vue", "node", "spring", "api rest", "restful", "json", "xml", "microsservicos",
            "microservicos", "git", "branch", "merge", "devops", "integracao continua", "ci/cd", "pipeline",
            "compilador", "funcao lambda", "variavel", "loop", "vetor", "array", "string", "codigo a seguir",
            "trecho de codigo", "programa a seguir", "pseudocodigo", "arquitetura de software", "acoplamento", "coesao",
            "ddd", "domain-driven", "ciclo de vida de desenvolvimento", "cmmi", "mps.br", "pontos de funcao",
            "manutencao de software", "qualidade de software", "iso/iec 25010", "android", "ios", "aplicativo movel",
            "aplicativos moveis", "mobile", "flutter", "swift", "regex", "expressao regular", "usabilidade",
            "acessibilidade", "wcag", "graphql", "rpa", "automacao robotica de processos", "paradigma", "paradigmas", "lista duplamente encadeada", "listas encadeadas", "utf-8", "ascii", "unicode", "hexadecimal", "complemento de dois", "complemento a dois", "gerenciamento de configuracao", "gerencia de configuracao", "versionamento", "controle de versao", "baseline", "compiladores", "orientado a objetos", "orientada a eventos", "api", "apis", "endpoint", "soap", "web service", "webservice", "frontend", "front-end", "backend", "back-end", "framework"],
        1: ["software", "programacao", "codigo", "funcao", "objeto", "classe", "teste", "requisito", "metodo", "web",
            "aplicacao", "biblioteca", "compilacao", "interpretador"]},
    "banco_de_dados_e_ciencia_de_dados": {
        2: ["sql", "select", "insert", "update", "delete from", "join", "group by", "having", "order by",
            "chave primaria", "chave estrangeira", "normalizacao", "forma normal", "1fn", "2fn", "3fn", "fnbc",
            "dependencia funcional", "modelo entidade", "entidade-relacionamento", "diagrama er", "cardinalidade", "sgbd",
            "banco de dados", "bancos de dados", "stored procedure", "trigger", "view", "acid", "commit", "rollback",
            "nosql", "mongodb", "cassandra", "redis", "postgresql", "oracle", "mysql", "sql server", "data warehouse",
            "datawarehouse", "data lake", "data mart", "olap", "etl", "elt", "modelagem dimensional", "tabela fato",
            "tabela dimensao", "star schema", "esquema estrela", "floco de neve", "business intelligence", "bi",
            "mineracao de dados", "data mining", "aprendizado de maquina", "machine learning", "aprendizado supervisionado",
            "nao supervisionado", "regressao linear", "regressao logistica", "clusterizacao", "k-means",
            "arvore de decisao", "random forest", "rede neural", "redes neurais", "deep learning", "overfitting",
            "acuracia", "revocacao", "matriz de confusao", "validacao cruzada", "f1-score", "big data", "hadoop", "spark",
            "pandas", "dataframe", "ciencia de dados", "cientista de dados", "inteligencia artificial", "llm",
            "processamento de linguagem natural", "algebra relacional", "analise exploratoria", "curtose",
            "desvio padrao", "variavel aleatoria", "distribuicao normal", "teste de hipotese", "intervalo de confianca",
            "series temporais", "juncao natural", "sistemas de informacoes geograficas", "sistema de informacao geografica", "geoprocessamento", "dados georreferenciados", "sig", "gis", "power bi", "dashboard", "dashboards", "governanca de dados", "qualidade de dados", "catalogo de dados", "metadados", "lakehouse", "dba", "replicacao de dados", "particionamento", "tupla", "relacional", "consulta sql"],
        1: ["dados", "coluna", "colunas", "tabela", "tabelas", "indice", "indices", "transacao", "atributo", "consulta",
            "classificacao", "agrupamento", "precisao", "analise de dados", "dataset", "base de dados"]},
    "redes_e_infraestrutura": {
        2: ["tcp", "udp", "ip", "ipv4", "ipv6", "osi", "camada de transporte", "camada de rede", "camada de enlace",
            "camada fisica", "roteador", "roteamento", "switch", "switches", "vlan", "hub", "gateway", "sub-rede",
            "subrede", "mascara", "cidr", "endereco ip", "enderecos ip", "dns", "dhcp", "http", "https", "ftp", "smtp",
            "pop3", "imap", "snmp", "ssh", "telnet", "arp", "icmp", "nat", "ospf", "bgp", "rip", "mpls", "ethernet",
            "wi-fi", "wifi", "wireless", "802.11", "802.3", "ieee", "csma/cd", "csma/ca", "sem fio", "wlan", "5g", "4g",
            "banda larga", "internet", "fibra", "cabeamento", "lan", "wan", "topologia", "largura de banda", "latencia",
            "qos", "voip", "h.323", "sip", "rtp", "sdn", "proxy", "vlans", "wlans", "roteadores", "firewalls", "balanceador de carga", "balanceamento de carga", "sistema operacional",
            "sistemas operacionais", "linux", "windows", "kernel", "escalonamento de processos", "processo filho",
            "thread", "threads", "escalonamento", "memoria virtual", "paginacao", "deadlock", "sistema de arquivos",
            "ntfs", "ext4", "shell", "bash", "powershell", "active directory", "ldap", "virtualizacao",
            "maquina virtual", "maquinas virtuais", "hypervisor", "hipervisor", "vmware", "docker", "container",
            "conteiner", "kubernetes", "computacao em nuvem", "nuvem", "cloud", "iaas", "paas", "saas", "aws", "azure",
            "storage", "storage san", "storage nas", "network attached storage", "raid", "backup", "data center",
            "datacenter", "servidor web", "servidor de aplicacao", "servidor dns", "servidor de arquivos",
            "servidor proxy", "cluster", "alta disponibilidade", "cpu", "processador", "memoria ram", "cache",
            "barramento", "arquitetura de computadores", "hardware", "impressora", "periferico", "bios", "uefi",
            "monitoramento", "zabbix", "nagios", "service desk", "suporte tecnico"],
        1: ["rede de computadores", "redes de computadores", "protocolo", "protocolos", "pacote", "pacotes", "porta",
            "portas", "conexao", "trafego", "comutacao", "host", "hosts", "memoria", "disco", "servidor", "servidores"]},
    "seguranca_da_informacao": {
        2: ["criptografia", "criptografica", "criptografico", "cifra", "cifragem", "simetrica", "assimetrica",
            "chave publica", "chave privada", "rsa", "aes", "3des", "hash criptografico", "sha", "md5",
            "assinatura digital", "certificado digital", "certificados digitais", "icp-brasil", "pki",
            "autoridade certificadora", "tls", "ssl", "ipsec", "vpn", "firewall", "ids", "ips", "siem", "waf", "dmz",
            "honeypot", "malware", "virus", "worm", "trojan", "cavalo de troia", "ransomware", "spyware", "rootkit",
            "botnet", "phishing", "engenharia social", "ataque", "ataques", "ddos", "negacao de servico",
            "sql injection", "injecao de sql", "xss", "cross-site", "csrf", "man-in-the-middle", "forca bruta",
            "vulnerabilidade", "vulnerabilidades", "exploit", "pentest", "teste de invasao", "owasp", "autenticacao",
            "autenticacao multifator", "mfa", "2fa", "oauth", "saml", "controle de acesso", "confidencialidade",
            "nao repudio", "iso 27001", "iso 27002", "iso/iec 27001", "iso/iec 27002", "27001", "27002", "27005",
            "gestao de riscos de seguranca", "incidente de seguranca", "incidentes de seguranca", "csirt", "lgpd",
            "protecao de dados", "dados pessoais", "anpd", "politica de seguranca", "seguranca da informacao",
            "ciberseguranca", "seguranca cibernetica", "zero trust", "nist", "cis controls", "continuidade de negocios",
            "gestao de continuidade", "rto", "rpo", "drp", "plano de recuperacao de desastres",
            "recuperacao de desastres", "continuidade do negocio", "plano de continuidade", "computacao forense", "forense", "pericia digital", "cadeia de custodia", "hardening", "backdoor", "keylogger", "sandbox", "antivirus", "biometria",
            "token", "senha", "senhas", "esteganografia"],
        1: ["seguranca", "ameaca", "ameacas", "invasor", "atacante", "sigilo", "acesso", "privacidade", "integridade",
            "disponibilidade", "risco", "riscos", "incidente", "incidentes"]},
    "governanca_e_gestao_de_ti": {
        2: ["cobit", "itil", "governanca de ti", "governanca corporativa de ti", "gestao de servicos de ti", "pmbok",
            "prince2", "gerenciamento de projetos", "gerente de projeto", "escopo do projeto", "caminho critico", "eap",
            "stakeholder", "bpm", "bpmn", "processo de negocio", "processos de negocio", "iso 20000", "iso/iec 38500",
            "38500", "balanced scorecard", "bsc", "pdti", "plano diretor de tecnologia da informacao",
            "acordo de nivel de servico", "contratacao de solucoes de ti", "in sgd", "in 94", "in 04", "okr",
            "catalogo de servicos", "gestao de mudancas", "gerenciamento de incidentes", "gerenciamento de problemas",
            "cadeia de valor de servico", "mapeamento de processos", "mapeamento de processo", "as-is", "to-be", "stic", "solucao de tic", "solucoes de tic", "contratacao de solucoes de tecnologia da informacao", "contratos de ti", "servicos de ti", "gerenciamento de riscos do projeto", "resposta ao risco", "gerenciamento de riscos", "escritorio de projetos", "pmo"],
        1: ["governanca", "projeto", "projetos", "partes interessadas", "maturidade", "melhoria continua", "portfolio",
            "sla", "kpi"]},
}
LIMIAR = 3

_PADROES = {area: [(peso, re.compile(r"(?<![\w])" + re.escape(norm(t)) + r"(?![\w])"))
                   for peso, termos in niveis.items() for t in termos]
            for area, niveis in SUBAREAS.items()}


def _preparar(texto):
    # expressão de redes que contém um termo de segurança ("controle de acesso")
    return re.sub(r"controle de acesso ao meio", "mac_camada_enlace csma/cd", norm(texto))


def pontuar(texto):
    """Termos de peso 2 contam cada ocorrência (até 3 vezes); termos de peso 1 contam só a presença,
    para que uma palavra genérica repetida ("dados", "projeto", "servidor") não decida sozinha."""
    t = _preparar(texto)
    sc = {}
    for a, pads in _PADROES.items():
        total = 0
        for p, rx in pads:
            n = len(rx.findall(t))
            total += p * min(n, 3) if p == 2 else (1 if n else 0)
        sc[a] = total
    return sc


def termos_fortes(texto, area):
    t = _preparar(texto)
    return sum(1 for p, rx in _PADROES[area] if p == 2 and rx.search(t))


def classificar(texto, secao_de_ti=False):
    """Exige ao menos um termo característico (peso 2) da subárea vencedora e pontuação >= 3
    (>= 2 quando a questão está numa seção de TI da prova)."""
    sc = pontuar(texto)
    area, s = max(sc.items(), key=lambda kv: kv[1])
    if not (termos_fortes(texto, area) >= 1 and (s >= LIMIAR or (secao_de_ti and s >= 2))):
        return None, sc
    # desempate: questões de segurança costumam vir num contexto de redes ou de software, cujos termos
    # genéricos inflam a pontuação dessas subáreas. Se segurança está a no máximo 1 ponto da vencedora e
    # a questão tem >= 2 termos característicos distintos de segurança, fica em segurança.
    seg = "seguranca_da_informacao"
    if area != seg and sc[seg] >= s - 1 and termos_fortes(texto, seg) >= 2:
        area = seg
    return area, sc
