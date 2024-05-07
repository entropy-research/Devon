
Mihir (more greennfield SWE focused)
- When the agent starts it should getvinformation necessary to make good descisions (IMP)
  - what folders, files exist what is their semantic puprose
- SWE related Information like: (NOT THAT IMPORTANT)
  - how to run tests
  - how to build
  - README and docs
  - linting and formatting config files
  


  
Kiran
Code search
- needs full awareness of entities (i.e. knowledge graph)
    - this means classes, functions, call graph, instances etc.
    - Needs some form of visual traceability or kg search for end user
    - needs to semantically & hierarchically index the repo
        - e.g. each entity (file, class, function etc.) needs a description and kg relationships to other things
            - if class A is referenced in doc.txt there should be a link
    - I want good ranking of related information so that I can ask:
        - what is ___ used for?
        - where is __ used?
        - How do I test with __ ? (if the thing has no tests it should have knowledge more generally of testing patterns in the repo and should be able to follow them/reccommend them)
        - I got this error: where are some places I could look?
            - this means direct symbol search also needs to exist (Globals, etc)
        - results should return in most relevant order, with descriptions, context, and potentially relations
    - I need to be able to locate all instances of ___ (with varying degrees of fuzzyness, think vscode search)
- I want a graph of some sort to visualize the search
- I need to be able to find "most relevant segments" for a given block of text be it a question, request, or even just a code block
- I want tunable reranking based on arbitrary natural language rules
    - i.e. I want to be able to say: tests aren't relevant for me right now, and it should ignore tests search
