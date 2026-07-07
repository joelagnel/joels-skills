# Mermaid Sequence Diagrams for Code Flow

Best for: Function call sequences, inter-thread communication, lock flows, callback chains.

A picture speaks a thousand words. Sequence diagrams excel at showing **code flow** - the sequence of events between different objects or entities. They answer: "What calls what, in what order, and why?"

## Basic Code Flow Example

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Thread<br/>(submit)
    participant Disp as Dispatcher<br/>(coordinator)
    participant Worker as Worker Thread<br/>(worker)

    rect rgb(200, 220, 255)
        Note over Client: Enqueue Phase
        Client->>Client: enqueue(job, handler)
        Client->>+Disp: wake_dispatcher()
    end

    Disp->>Disp: Wait for batch window
    Disp-->>Worker: Signal batch ready

    rect rgb(255, 220, 200)
        Note over Worker: Execution Phase
        Worker->>Worker: handle(job)
    end
```

## Advanced Code Flow Techniques (advanced)

### 1. Trace Event Annotations

Embed actual tracepoint names inline:

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Thread
    participant Disp as Dispatcher

    Client->>Client: submit(job, handler)
    Note over Client: trace: job_submitted
    Client->>+Disp: notify_dispatcher()
    Note over Disp: trace: dispatcher_woken
```

### 2. State Variable Changes

Show state variable mutations:

```mermaid
sequenceDiagram
    participant Handler as Request Handler
    participant Lock as Lock Manager

    Handler->>Lock: release_lock()
    Lock->>Lock: refcount--
    Lock->>Lock: held = 0
    Lock->>Lock: Add to lock->wait_list
```

### 3. Conditional Paths with alt/else

```mermaid
sequenceDiagram
    participant Client as Client
    participant Disp as Dispatcher

    Client->>Client: submit_job_and_wake()

    alt queue was empty
        Note over Client: trace: wake_empty
        Client->>Disp: signal_dispatcher()
    else queue had pending jobs
        Note over Client: trace: wake_not_empty
        Note over Client: No wake needed
    end
```

### 4. Daemon Loop Patterns

```mermaid
sequenceDiagram
    participant Disp as Dispatcher

    loop Forever
        Disp->>Disp: wait_event(dispatch_wq)
        loop For each queue in my_queues
            Disp->>Disp: dispatch_wait(queue)
            alt jobs ready
                Disp->>Disp: advance_batch()
            end
        end
    end
```

### 5. Multi-Thread Lifecycle (Complete Example)

```mermaid
sequenceDiagram
    autonumber
    participant Client as Client Thread<br/>(startup)
    participant Disp as Dispatcher/X<br/>(batch coordinator)
    participant Batch as batch_engine<br/>(main batch loop)
    participant Worker as Worker/Y<br/>(worker thread)

    rect rgb(200, 220, 255)
        Note over Client: Phase 1: Enqueue
        Client->>Client: submit(job, handler)
        Client->>Client: accept_job()
        Client->>Client: enqueue_job()
        Client->>+Disp: notify_dispatcher()
    end

    rect rgb(220, 255, 220)
        Note over Disp: Phase 2: Batch Request
        Disp->>Disp: dispatch_wait()
        Disp->>+Batch: wake_batch_engine()
    end

    rect rgb(255, 255, 200)
        Note over Batch: Phase 3: Batch Window (a few ms)
        Batch->>Batch: batch_init()
        Batch->>Batch: batch_collect_loop()
        Batch->>Batch: batch_cleanup()
        Batch-->>-Disp: signal_all()
    end

    rect rgb(255, 220, 200)
        Note over Worker: Phase 4: Job Execution
        Disp->>+Worker: wake worker thread
        Worker->>Worker: process_batch()
        loop For each job
            Worker->>Worker: handle(job)
        end
        Worker-->>-Client: complete(done)
    end
```

## Color Conventions

| Color | RGB | Use For |
|-------|-----|---------|
| Blue | `rgb(200, 220, 255)` | Entry/enqueue phases |
| Green | `rgb(220, 255, 220)` | Processing phases |
| Yellow | `rgb(255, 255, 200)` | Wait/deferral periods |
| Orange | `rgb(255, 220, 200)` | Execution/completion |
| Red | `rgb(255, 200, 200)` | Interrupt/signal events |

## Syntax Reference

| Feature | Syntax | Description |
|---------|--------|-------------|
| Autonumber | `autonumber` | Auto step numbers |
| Colored region | `rect rgb(R, G, B)` | Phase highlighting |
| Rich participant | `participant X as Label<br/>subtitle` | Multi-line names |
| Solid arrow | `->>` | Synchronous call |
| Dashed arrow | `-->>` | Response/async |
| Activate | `+` after arrow | Start lifeline |
| Deactivate | `-` after arrow | End lifeline |
| Conditional | `alt/else/end` | Branch paths |
| Loop | `loop Label` | Iteration |
| Note | `Note over X: text` | Annotation |

## Flowcharts (Graph Diagrams)

Best for: Decision trees, control flow, algorithm visualization.

```mermaid
graph TD
    subgraph "Input Validation"
        A[Start] --> B{Valid input?}
        B -->|Yes| C[Process]
        B -->|No| D[Error]
    end

    subgraph "Processing"
        C --> E{Check condition}
        E -->|True| F[Action A]
        E -->|False| G[Action B]
    end

    F --> H[End]
    G --> H
    D --> H
```

**Direction options:** `TD` (top-down), `LR` (left-right), `BT` (bottom-top), `RL` (right-left)

**Node shapes:**
- `[text]` - Rectangle
- `(text)` - Rounded rectangle
- `{text}` - Diamond (decision)
- `((text))` - Circle
- `[[text]]` - Subroutine
- `[(text)]` - Cylinder (database)

## Class Diagrams

Best for: Struct relationships, API interfaces, component dependencies.

```mermaid
classDiagram
    class JobQueue {
        +job_list jobs
        +bypass_queue bypass
        +dispatcher_thread dispatcher
        +enqueue_job()
        +flush_bypass()
    }

    class JobList {
        +head: job*
        +tails[4]: job**
        +seglen[4]: long
        +advance_jobs()
        +extract_jobs()
    }

    JobQueue --> JobList : contains
```
