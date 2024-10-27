from crewai import Agent, Crew, Process, Task

class RevisorArtigosSl3V1Crew:
    """
    RevisorArtigosSl3V1Crew - Equipe para ler e revisar PDFs

    Esta classe representa uma equipe (Crew) especializada em ler e revisar PDFs,
    utilizando modelos de linguagem (LLMs) e ferramentas específicas de leitura de PDFs.
    A classe é configurada com agentes e tarefas definidos nos arquivos YAML de configuração.
    """

    def __init__(self, agents_config=None, tasks_config=None, llm=None, pdf_tool=None):
        """
        Inicializa a equipe com as configurações necessárias.

        Args:
            agents_config (dict, opcional): Configurações dos agentes do arquivo agents.yaml.
            tasks_config (dict, opcional): Configurações das tarefas do arquivo tasks.yaml.
            llm: Modelo de linguagem a ser usado pelos agentes.
            pdf_tool: Ferramenta para leitura de PDFs, utilizada pelo agente Leitor.

        Atributos:
            agents_config (dict): Armazena as configurações dos agentes.
            tasks_config (dict): Armazena as configurações das tarefas.
            llm: Instância do modelo de linguagem a ser usada pelos agentes.
            pdf_tool: Instância da ferramenta de leitura de PDFs.
        """
        self.agents_config = agents_config or {}
        self.tasks_config = tasks_config or {}
        self.llm = llm
        self.pdf_tool = pdf_tool

    def _create_leitor_pdfs(self):
        """
        Cria o agente Leitor de PDFs usando a configuração do agents.yaml.

        Este agente é responsável por ler PDFs e extrair informações conforme
        definido na configuração dos agentes.

        Returns:
            Agent: Instância do agente configurado para leitura de PDFs.
        """
        agent_config = self.agents_config.get('leitor_pdfs', {})

        return Agent(
            role=agent_config.get('role'),
            goal=agent_config.get('goal'),
            backstory=agent_config.get('backstory'),
            tools=[self.pdf_tool] if self.pdf_tool else [],
            llm=self.llm,
            verbose=True
        )

    def _create_revisor_yaml(self):
        """
        Cria o agente Revisor de YAML usando a configuração do agents.yaml.

        Este agente é responsável por revisar o YAML gerado pelo agente Leitor,
        garantindo que esteja em conformidade com o template especificado.

        Returns:
            Agent: Instância do agente configurado para revisão de YAML.
        """
        agent_config = self.agents_config.get('revisor_yaml', {})

        return Agent(
            role=agent_config.get('role'),
            goal=agent_config.get('goal'),
            backstory=agent_config.get('backstory'),
            llm=self.llm,
            verbose=True
        )

    def create_crew(self):
        """
        Cria e retorna a equipe configurada usando as definições dos YAMLs.

        A equipe (Crew) é composta por dois agentes: um Leitor de PDFs e um Revisor de YAML.
        Cada agente realiza uma tarefa específica, e as tarefas são executadas de forma
        sequencial, onde a tarefa de revisão depende da conclusão da tarefa de leitura.

        Returns:
            Crew: Instância da equipe configurada para processamento de PDFs.
        """
        # Criar os agentes
        leitor = self._create_leitor_pdfs()
        revisor = self._create_revisor_yaml()

        # Criar as tarefas usando as configurações do tasks.yaml
        leitura_config = self.tasks_config.get('leitura_pdfs', {})
        revisao_config = self.tasks_config.get('revisao_yaml', {})

        # Criar a tarefa de leitura de PDFs
        leitura = Task(
            description=leitura_config.get('description', ''),
            expected_output=leitura_config.get('expected_output', ''),
            agent=leitor
        )

        # Criar a tarefa de revisão de YAML
        revisao = Task(
            description=revisao_config.get('description', ''),
            expected_output=revisao_config.get('expected_output', ''),
            agent=revisor,
            context=[leitura]  # A tarefa de revisão depende da conclusão da leitura
        )

        # Criar e retornar a equipe (Crew)
        return Crew(
            agents=[leitor, revisor],
            tasks=[leitura, revisao],
            process=Process.sequential,  # Define o processo sequencial de execução
            verbose=True
        )
