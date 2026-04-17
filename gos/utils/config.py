from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GOS_",
        extra="ignore",
    )

    WORKING_DIR: str = "./gos_workspace"
    PREBUILT_WORKING_DIR: str | None = None
    DOMAIN: str = "Agent Skills and Tool Dependencies"

    LLM_MODEL: str = "gemini/gemini-3.1-flash-lite-preview"
    EMBEDDING_MODEL: str = "openai/text-embedding-3-large"
    EMBEDDING_DIM: int = 3072
    GEMINI_API_KEY: SecretStr | None = Field(default=None, alias="GEMINI_API_KEY")
    OPENAI_API_KEY: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    OPENROUTER_API_KEY: SecretStr | None = Field(default=None, alias="OPENROUTER_API_KEY")
    OPENAI_BASE_URL: str | None = Field(default=None, alias="OPENAI_BASE_URL")

    LINK_TOP_K: int = 8
    SEED_TOP_K: int = 5
    RETRIEVAL_TOP_N: int = 8
    USE_FULL_MARKDOWN: bool = True
    ENABLE_SEMANTIC_LINKING: bool = True
    DEPENDENCY_MATCH_THRESHOLD: float = 0.6

    PPR_DAMPING: float = 0.2
    PPR_MAX_ITER: int = 50
    PPR_TOLERANCE: float = 1e-6

    SNIPPET_CHARS: int = 900
    MAX_SKILL_CHARS: int = 2400
    MAX_CONTEXT_CHARS: int = 12000
    RERANK_CANDIDATE_MULTIPLIER: int = 4
    SEED_CANDIDATE_TOP_K_SEMANTIC: int = 20
    SEED_CANDIDATE_TOP_K_LEXICAL: int = 20
    ENABLE_QUERY_REWRITE: bool = False

    SKILL_FILENAME: str = "SKILL.md"
    ALLOW_FRONTMATTER_DOCS: bool = True

    # Primitive-edge generation knobs: deterministic edges from shared primitives
    # (tooling, domain tags, allowed tools, compatibility, inputs/outputs) raise
    # edge density without paying an LLM call per pair.
    ENABLE_PRIMITIVE_EDGES: bool = True
    PRIMITIVE_EDGE_MIN_OVERLAP: int = 2
    PRIMITIVE_EDGE_MIN_JACCARD: float = 0.35
    PRIMITIVE_EDGE_MAX_PER_SOURCE: int = 12
    # Loose I/O overlap threshold used only for primitive workflow edges.
    # The strict dependency threshold (DEPENDENCY_MATCH_THRESHOLD) is untouched.
    PRIMITIVE_WORKFLOW_THRESHOLD: float = 0.3
    # Document-frequency ceiling for primitive tokens. Tokens present in more
    # than this fraction of skills are discarded before overlap scoring — they
    # are corpus-wide and carry no discriminating signal (e.g. `bash`, `read`,
    # `write` in a Claude Code library, or parse-noise word-splits from
    # multi-word domain tags). Set to 1.0 to disable.
    PRIMITIVE_TOKEN_DF_MAX: float = 0.3

    # Name co-mention edges: when one skill's body explicitly names another.
    ENABLE_NAME_COMENTION_EDGES: bool = True

    # Family edges: skills sharing a hyphen-prefix (e.g. `breadcrumbs-*`).
    ENABLE_FAMILY_EDGES: bool = True
    FAMILY_EDGE_MAX_PER_SOURCE: int = 6
    # When a pair of skills only shares a 1-token prefix, emit the family edge
    # only if that shallow family has <= this many members. Prevents broad
    # namespaces (e.g. `obsidian-*` with 25 skills spanning plugin dev, canvas,
    # cron, bases, devtools) from gluing unrelated subdomains together. Pairs
    # sharing a deeper prefix (e.g. `obsidian-plugin-shadcn-*`) always emit.
    FAMILY_SHALLOW_MAX_SIZE: int = 8
    # Maximum prefix depth (hyphen tokens) to consider when looking for a
    # deeper-than-1 shared prefix. 3 is enough for `obsidian-plugin-shadcn-*`
    # style hierarchies; going deeper increases fragmentation without signal.
    FAMILY_MAX_PREFIX_DEPTH: int = 3

    # When set, graphskills-query rewrites Source: paths to {SKILLS_DIR}/{skill_name}/SKILL.md
    # so agents in containerised environments can find skill scripts at the mounted path.
    SKILLS_DIR: str = ""


settings = Settings()
