# 🏗️ Substratos Técnicos de Plataforma

Os **Substratos** são adaptadores de plataforma que olham para o Sistema Operacional e infraestrutura física, fornecendo suporte vital a todo o sistema.

---

## 🏛️ Os Três Substratos do Segmento de Solo

1. **Substrato de Ambiente & Execução (`infrastructure/runtime/`):**
   * Desacopla o sistema de ferramentas externas e isolamentos de runtime.
   * `NativeDriver`: execução nativa no SO via subprocessos.
   * `VirtualEnvDriver`: execução contextualizada no ambiente `.venv`.
   * `ContainerDriver`: execução transparente em contêineres OCI (Podman/Docker).
   * `EnvironmentSubstrate`: fachada unificada com fallback automático (`auto`, `native`, `venv`, `container`).

2. **Substrato de Configuração (`infrastructure/config/`):**
   * Centraliza parâmetros canônicos e resolve configuração em cascata de 4 níveis:
     $$\text{Defaults em Código} \to \text{YAML (ground\_parameters.yaml)} \to \text{Variáveis de Ambiente (RPS\_GROUND\_*)} \to \text{Overrides}$$
   * Singleton thread-safe `ConfigurationSubstrate.get_instance()`.

3. **Substrato de Persistência Espacial (`infrastructure/persistence/`):**
   * Gerencia conexões PostgreSQL/PostGIS, pool `QueuePool` com `pool_pre_ping=True`, context manager `session_scope()` com garantia ACID e verificações de liveness não-bloqueantes (`health_check()`).
