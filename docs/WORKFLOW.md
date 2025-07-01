# ��� WhatsApp AI Assistant - Workflow Documentation

## Message Processing Workflow

```mermaid
flowchart TD
    A[WhatsApp User sends message] --> B[Go Bridge receives message]
    B --> C[Store in SQLite database]
    C --> D[Message Processor polls every 3s]
    D --> E{Check for triggers?}
    E -->|No triggers| F[Ignore message]
    E -->|Has trigger| G[Extract query from message]
    G --> H[Route to Agent Orchestrator]
    H --> I[Calculate confidence scores]
    I --> J{Best agent found?}
    J -->|No| K[Use fallback response]
    J -->|Yes| L[Send to selected agent]
    L --> M[Agent processes with AI]
    M --> N[Generate response]
    N --> O[Send back to Message Processor]
    O --> P[Send via Bridge API]
    P --> Q[User receives response in WhatsApp]
    
    style G fill:#e1f5fe
    style H fill:#f3e5f5
    style L fill:#e8f5e8
    style M fill:#fff3e0
    style Q fill:#e8f5e8
```

## Trigger Detection Process

```mermaid
flowchart LR
    A[Incoming Message] --> B{Starts with trigger?}
    B -->|!ask| C[Extract query after '!ask']
    B -->|@bot| D[Extract query after '@bot']
    B -->|@ai| E[Extract query after '@ai']
    B -->|>| F[Extract query after '>']
    B -->|No trigger| G[Ignore message]
    
    C --> H[Route to Orchestrator]
    D --> H
    E --> H
    F --> H
    
    style B fill:#fff3e0
    style H fill:#e1f5fe
```

## Agent Selection Workflow

```mermaid
flowchart TD
    A[Message arrives at Orchestrator] --> B[Load Agent Registry]
    B --> C[For each enabled agent]
    C --> D[Call agent.can_handle(message)]
    D --> E[Get confidence score 0.0-1.0]
    E --> F{More agents to check?}
    F -->|Yes| C
    F -->|No| G[Select agent with highest confidence]
    G --> H{Confidence > 0.5?}
    H -->|Yes| I[Route to selected agent]
    H -->|No| J[Use default Q&A agent]
    
    style G fill:#e1f5fe
    style I fill:#e8f5e8
    style J fill:#fff3e0
```

## Multi-Agent Response Flow

```mermaid
sequenceDiagram
    participant User as WhatsApp User
    participant Bridge as Go Bridge
    participant Processor as Message Processor
    participant Orchestrator as Agent Orchestrator
    participant QnA as Q&A Agent
    participant CodeAgent as Code Agent
    participant SearchAgent as Search Agent
    participant Gemini as Gemini API
    
    User->>Bridge: !ask What is Python?
    Bridge->>Processor: Poll for new messages
    Processor->>Orchestrator: Route message
    
    par Agent Confidence Scoring
        Orchestrator->>QnA: can_handle("What is Python?")
        QnA-->>Orchestrator: confidence: 0.85
    and
        Orchestrator->>CodeAgent: can_handle("What is Python?")
        CodeAgent-->>Orchestrator: confidence: 0.90
    and
        Orchestrator->>SearchAgent: can_handle("What is Python?") 
        SearchAgent-->>Orchestrator: confidence: 0.40
    end
    
    Orchestrator->>CodeAgent: process(message) [highest confidence]
    CodeAgent->>Gemini: Generate code-focused response
    Gemini-->>CodeAgent: Python programming language explanation
    CodeAgent-->>Orchestrator: AgentResponse
    Orchestrator-->>Processor: Final response
    Processor->>Bridge: Send response
    Bridge->>User: Detailed Python explanation
```

## System Startup Workflow

```mermaid
flowchart TD
    A[Start main.py] --> B[Load environment configuration]
    B --> C[Initialize logging system]
    C --> D[Check environment requirements]
    D --> E{All requirements met?}
    E -->|No| F[Exit with error message]
    E -->|Yes| G[Initialize Agent Orchestrator]
    G --> H[Load agent registry]
    H --> I[Initialize all enabled agents]
    I --> J[Start Message Processor]
    J --> K[Connect to WhatsApp Bridge]
    K --> L{Bridge connected?}
    L -->|No| M[Retry connection]
    L -->|Yes| N[Start polling loop]
    N --> O[System ready - processing messages]
    
    style G fill:#e1f5fe
    style I fill:#e8f5e8
    style O fill:#4caf50,color:#ffffff
```

## Dashboard Interaction Workflow

```mermaid
flowchart LR
    A[User opens Dashboard] --> B[Check Bridge connection]
    B --> C{Bridge online?}
    C -->|No| D[Show connection guide]
    C -->|Yes| E[Check WhatsApp status]
    E --> F{WhatsApp connected?}
    F -->|No| G[Show QR code instructions]
    F -->|Yes| H[Load recent messages]
    H --> I[Display agent statistics]
    I --> J[Enable message sending]
    
    J --> K[User sends test message]
    K --> L[Route through orchestrator]
    L --> M[Display response]
    
    style H fill:#e1f5fe
    style J fill:#e8f5e8
    style M fill:#4caf50,color:#ffffff
```

## Error Handling Workflow

```mermaid
flowchart TD
    A[Error occurs] --> B{Error type?}
    B -->|Bridge connection| C[Retry connection with backoff]
    B -->|Agent processing| D[Use fallback response]
    B -->|Gemini API| E[Switch to LangChain fallback]
    B -->|Configuration| F[Log error and exit]
    
    C --> G{Retry successful?}
    G -->|Yes| H[Resume normal operation]
    G -->|No| I[Show connection guide]
    
    D --> J[Generate helpful error message]
    E --> K[Continue with alternative model]
    
    style J fill:#fff3e0
    style H fill:#4caf50,color:#ffffff
    style I fill:#ff9800,color:#ffffff
```

## Configuration Loading Workflow

```mermaid
flowchart LR
    A[Application starts] --> B[Load .env file]
    B --> C[Check environment variables]
    C --> D[Override with system env vars]
    D --> E[Validate required settings]
    E --> F{Valid configuration?}
    F -->|No| G[Show configuration errors]
    F -->|Yes| H[Load agent registry.json]
    H --> I[Validate agent configurations]
    I --> J[Initialize system with settings]
    
    style E fill:#fff3e0
    style J fill:#4caf50,color:#ffffff
    style G fill:#f44336,color:#ffffff
```

## Message Types and Routing

### Personal Chat Messages
```
Format: !ask [query]
Example: "!ask What is machine learning?"
Flow: User → Bridge → Processor → Orchestrator → Agent → Response
```

### Group Chat Messages  
```
Format: @bot [query] or @ai [query]
Example: "@bot Explain quantum computing"
Flow: Group → Bridge → Processor → Orchestrator → Agent → Group
```

### Dashboard Messages
```
Format: Direct input via web interface
Flow: Dashboard → Orchestrator → Agent → Dashboard display
```

## Performance Optimization Workflow

```mermaid
flowchart TD
    A[Message received] --> B[Quick trigger check]
    B --> C{Is trigger present?}
    C -->|No| D[Early return - ignore]
    C -->|Yes| E[Async processing]
    E --> F[Parallel agent scoring]
    F --> G[Select best agent]
    G --> H[Process with timeout]
    H --> I{Response within timeout?}
    I -->|No| J[Return timeout message]
    I -->|Yes| K[Return agent response]
    
    style E fill:#e1f5fe
    style F fill:#f3e5f5
    style H fill:#fff3e0
```

## Logging and Monitoring Workflow

```mermaid
flowchart LR
    A[System event occurs] --> B[Determine log level]
    B --> C{Console logging enabled?}
    C -->|Yes| D[Format for console with colors]
    C -->|No| E[Skip console output]
    
    D --> F[Display in terminal]
    E --> G{File logging enabled?}
    G -->|Yes| H[Write to daily log file]
    G -->|No| I[Skip file logging]
    
    F --> G
    H --> J[Rotate logs daily]
    J --> K[Retain logs for 7 days]
    
    style F fill:#e1f5fe
    style H fill:#e8f5e8
    style K fill:#fff3e0
```

This workflow documentation provides a comprehensive view of how messages flow through the WhatsApp AI Assistant system, from initial reception to final response delivery.
