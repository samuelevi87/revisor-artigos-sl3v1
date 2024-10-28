import logging
import os
import re
from pathlib import Path

from crewai import Agent, Crew, Process, Task


class RevisorArtigosSl3V1Crew:
    """
    RevisorArtigosSl3V1Crew - Equipe para ler e revisar PDFs

    Esta classe representa uma equipe (Crew) especializada em ler e revisar PDFs,
    utilizando modelos de linguagem (LLMs) e ferramentas específicas de leitura de PDFs.
    A classe é configurada com agentes e tarefas definidos nos arquivos YAML de configuração.
    """

    def __init__(self, agents_config=None, tasks_config=None, llm=None, pdf_tool=None, serper_tool=None):
        """
        Inicializa a equipe com as configurações necessárias.

        Args:
            agents_config (dict, opcional): Configurações dos agentes do arquivo agents.yaml.
            tasks_config (dict, opcional): Configurações das tarefas do arquivo tasks.yaml.
            llm: Modelo de linguagem a ser usado pelos agentes.
            pdf_tool: Ferramenta para leitura de PDFs, utilizada pelo agente Leitor.
            serper_tool: Ferramenta para buscar informações adicionais, utilizada pelo agente Criador de Artigos.

        Atributos:
            agents_config (dict): Armazena as configurações dos agentes.
            tasks_config (dict): Armazena as configurações das tarefas.
            llm: Instância do modelo de linguagem a ser usada pelos agentes.
            pdf_tool: Instância da ferramenta de leitura de PDFs.
            serper_tool: Instância da ferramenta para buscar informações adicionais.
        """
        self.agents_config = agents_config or {}
        self.tasks_config = tasks_config or {}
        self.llm = llm
        self.pdf_tool = pdf_tool
        self.serper_tool = serper_tool

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
            verbose=True,
            memory=True
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

    def _create_agente_pesquisa(self):
        """
        Cria o agente de Pesquisa usando a configuração do agents.yaml.

        Este agente é responsável por realizar pesquisas adicionais sobre o tema abordado no artigo,
        utilizando a SerperDevTool para obter informações complementares que enriquecem o artigo final.

        Returns:
            Agent: Instância do agente configurado para realizar pesquisas adicionais.

        Raises:
            ValueError: Se qualquer configuração obrigatória estiver ausente ou inválida.
        """
        agent_config = self.agents_config.get('agente_pesquisa', {})

        # Validação das configurações
        role = agent_config.get('role')
        goal = agent_config.get('goal')
        backstory = agent_config.get('backstory')

        if not all([role, goal, backstory]):
            raise ValueError("Configuração inválida para o agente de pesquisa. "
                             "Certifique-se de que 'role', 'goal' e 'backstory' estão definidos.")

        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=[self.serper_tool] if self.serper_tool else [],
            llm=self.llm,
            verbose=True,
            memory=True
        )

    def _create_criador_artigos(self):
        """
        Cria o agente Criador de Artigos LinkedIn usando a configuração do agents.yaml.

        Este agente é responsável por criar um artigo para o LinkedIn, com base nos dados
        revisados e nas informações adicionais coletadas. O agente é configurado para:
        - Transformar dados técnicos em conteúdo engajante
        - Manter a precisão das informações científicas
        - Criar narrativas envolventes para o público do LinkedIn

        Args:
            None: Utiliza as configurações armazenadas em self.agents_config

        Returns:
            Agent: Instância do agente configurado para criar artigos no LinkedIn
                - role: Define a função do agente como criador de conteúdo
                - goal: Estabelece os objetivos de criação de artigos (sanitizado)
                - backstory: Fornece contexto e experiência ao agente
                - llm: Modelo de linguagem para processamento de texto
                - verbose: Ativa logs detalhados para debugging

        Raises:
            KeyError: Se configurações essenciais estiverem ausentes no agents.yaml
            ValueError: Se o goal ou role forem inválidos após sanitização

        Example:
            >>> criador = self._create_criador_artigos()
            >>> print(f"Agente criado com role: {criador.role}")
            Agente criado com role: Criador de Artigos LinkedIn
        """
        agent_config = self.agents_config.get('criador_artigos_linkedin', {})

        # Sanitizar o goal para remover dependências de variáveis não fornecidas
        goal = agent_config.get('goal', '')
        if '{solicitacoes}' in goal:
            goal = goal.replace('{solicitacoes}', '')

        # Validar configurações essenciais
        if not agent_config.get('role'):
            raise KeyError("Role não definido para o Criador de Artigos LinkedIn")

        if not goal.strip():
            raise ValueError("Goal inválido após sanitização")

        return Agent(
            role=agent_config.get('role'),
            goal=goal,
            backstory=agent_config.get('backstory'),
            llm=self.llm,
            verbose=True
        )

    def create_crew(self, output_file_artigo: str):
        """
            Cria e retorna a equipe configurada usando as definições dos YAMLs.

            A equipe (Crew) é composta por quatro agentes que trabalham de forma sequencial:

            1. **Leitor de PDFs:** Extrai informações do PDF com base nas solicitações definidas,
               gerando um output no formato YAML.
            2. **Revisor de YAML:** Valida o conteúdo YAML extraído, garantindo que esteja conforme
               o template especificado.
            3. **Agente de Pesquisa:** Realiza pesquisa adicional sobre o tema abordado no artigo,
               utilizando a SerperDevTool para enriquecer o conteúdo.
            4. **Criador de Artigos:** Gera um artigo para o LinkedIn, utilizando os dados revisados
               e as informações adicionais obtidas pelo agente de pesquisa.

            O salvamento dos arquivos é gerenciado centralmente pela função save_article(),
            que garante a consistência na nomeação e localização dos arquivos gerados.

            Returns:
                Crew: Instância da equipe configurada com todos os agentes e tarefas necessários
                      para o processamento completo dos artigos.

            Raises:
                ValueError: Se as configurações essenciais dos agentes ou tarefas estiverem ausentes
                KeyError: Se houver problemas com as chaves de configuração

            Example:
                >>> crew_instance = RevisorArtigosSl3V1Crew(agents_config, tasks_config, llm)
                >>> crew = crew_instance.create_crew()
                >>> results = crew.kickoff(inputs=inputs)
        """

        # Criar os agentes
        leitor = self._create_leitor_pdfs()
        revisor = self._create_revisor_yaml()
        agente_pesquisa = self._create_agente_pesquisa()
        criador_artigos = self._create_criador_artigos()

        # Obter configurações de cada tarefa
        leitura_config = self.tasks_config.get('leitura_pdfs', {})
        revisao_config = self.tasks_config.get('revisao_yaml', {})
        pesquisa_config = self.tasks_config.get('pesquisa_informacoes', {})
        criar_artigo_config = self.tasks_config.get('criar_artigo_linkedin', {})

        # Tarefa de leitura com output_file especificado
        leitura = Task(
            description=leitura_config.get('description', ''),
            expected_output=leitura_config.get('expected_output', ''),
            agent=leitor,
            output_format="YAML",  # Especifica formato de saída
        )

        # Tarefa de revisão com output_file especificado
        revisao = Task(
            description=revisao_config.get('description', ''),
            expected_output=revisao_config.get('expected_output', ''),
            agent=revisor,
            context=[leitura],
            output_format="YAML"  # Especifica formato de saída
        )

        # Tarefa de pesquisa adicional
        pesquisa = Task(
            description=pesquisa_config.get('description', ''),
            expected_output=pesquisa_config.get('expected_output', ''),
            agent=agente_pesquisa,
            context=[revisao],
            output_format="TEXT"
        )

        # Tarefa de criação de artigo no LinkedIn
        criar_artigo = Task(
            description=criar_artigo_config.get('description', ''),
            expected_output=criar_artigo_config.get('expected_output', ''),
            agent=criador_artigos,
            context=[revisao, pesquisa],
            output_format="markdown",  # Especifica formato de saída
            output_file=output_file_artigo  # Recebe o nome do arquivo dos inputs
        )

        # Criar e retornar a equipe com configurações adicionais
        return Crew(
            agents=[leitor, revisor, agente_pesquisa, criador_artigos],
            tasks=[leitura, revisao, pesquisa, criar_artigo],
            process=Process.sequential,
            verbose=True,
            full_output=True,  # Retorna todos os outputs intermediários
            cache=True  # Habilita cache para melhor performance
        )
