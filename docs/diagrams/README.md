# Diagrams

| Diagram | Notation | |
|---|---|---|
| Architecture at three levels: context, containers, components | C4 | [c4.md](c4.md) |
| Handling a deviation, AS-IS and TO-BE | BPMN 2.0 | [process-deviation-handling.md](process-deviation-handling.md) |
| Producing and signing the act | BPMN 2.0 | [process-act-signing.md](process-act-signing.md) |
| Detecting a deviation, as designed and as implemented | UML sequence | [sequence-deviation-detection.md](sequence-deviation-detection.md) |
| Use cases by role | UML use case | [use-cases.md](use-cases.md) |

The entity-relationship diagrams live with the
[data model](../data-model/README.md), since they are read alongside its notes.

## Sources and exports

Diagrams are kept as text wherever the notation allows it, so that they are
versioned, reviewable line by line, and cannot be lost with the tool that drew
them:

- **Sequence and ER diagrams** are Mermaid, written inline in the Markdown.
  GitHub renders them, so there is nothing to export.
- **C4 and use case diagrams** are PlantUML in [src](src), rendered to
  [export](export). C4 uses the C4-PlantUML library bundled with PlantUML. To
  regenerate after an edit:

  ```
  java -jar plantuml.jar -tpng -o ../export docs/diagrams/src/*.puml
  ```

- **BPMN diagrams** are PNG exports in [export](export). BPMN carries layout
  information that is not practical to maintain by hand, so the modelling tool
  stays the source for these two.
