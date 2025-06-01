import re




import re

import re

def check(generated_text):
    pattern = re.compile(r"Current message from\s+[^:]+:\s*[^\n]+\r?\n\s*Dune:\s*(.*?)(?:\r?\n\s*Output:\s*(.*?))?(?=\r?\n(?:[A-Za-z0-9]+:|Current message from)|$)", re.DOTALL | re.IGNORECASE)
    
    m = pattern.search(generated_text)
    if not m:
        print("No “Current message…: Dune:” block found (or user text was empty).")
        return

    dune_text = m.group(1).strip()
    print("Dune reply:", dune_text)

    output_text = m.group(2)
    if output_text is not None:
        print("Output text:", output_text.strip())

test_cases = [
    # 1. Proper Dune and Output adjacent
    """Current message from Alice: Hi Bob, how are you?
Dune: Hello there. I have a message.

Output: This is the result you were looking for.

Bob: Cool.""",

    # 2. Multiline Dune, then Output
    """Current message from Zoe: Just checking in with some updates.
Dune: I have a multiline reply.
Here is the second line.

Output: Computation complete.

System: Status updated.""",

    # 3. Dune reply present, but no Output
    """Current message from Charlie: Wanted to ask about the latest.
Dune: Only Dune replies here.

Anna: What happens next?""",

    # 4. Dune present, but a different speaker intervenes before Output
    """Current message from Taylor: Sharing my thoughts on the project.
Dune: This is something important.

George: Interruption!

Output: Late output should not be captured.

Viewer: Next speaker.""",

    # 5. Originally had no header; now fixed and added text after header
    """Current message from Mike: I'm just writing a quick line here.
Dune: I am here without the usual introduction.

Output: Should not be matched.

Alice: Following text.""",

    # 6. Dune and Output back-to-back with leading/trailing whitespace
    """Current message from Joy: Hey team, progress report below.
    Dune:     Something profound.     

     Output:    It worked, here's the output.    

User: Great!""",

    # 7. Dune at end of string, no Output, added next speaker
    """Current message from User: Testing the end case.
Dune: I'm the last speaker.

Alice: Following text.""",

    # 8. Complex spacing and case insensitivity
    """Current MESSAGE from Admin: system check in progress.
dune: This is in lowercase but still valid.

output: Outputs are also lowercase friendly.

Next: Done.""",

    # 9. Header present, but no Dune; only Output (should not match)
    """Current message from Steve: Just a status update.
Status: All clear.

Output: Something without a Dune.

User: Done.""",

    # 10. Dune and Output with symbols and line breaks
    """Current message from Operator: Checking symbol handling now.
Dune: Result -> ✓
Newlines
are also fine!

Output: ✔️ Operation successful
Details logged.

Admin: End.""",

    # 11. First Dune+Output, then second Dune without Output
    """Current message from User1: Starting the sequence here.
Dune: First message from Dune.
Output: First output.

Current message from User2: Continuing with a second message.
Dune: Second message from Dune without output.
Charlie: Next speaker.""",

    # 12. Dune then intervening speaker before Output
    """Current message from Admin: Admin notes at the top.
Dune: Important note from Dune.

Moderator: Interrupting comment.

Output: Late output should not be captured.

Viewer: Next.""",

    # 13. Multiple "Current message" blocks; only first Dune+Output should be captured
    """Current message from A: First header text here.
Dune: Alpha reply.
Output: Alpha result.

Current message from B: Second header text here.
Dune: Beta reply.
Output: Beta result.

Current message from C: Third header text here.
Dune: Gamma reply without output.
Carl: Next.""",

    # 14. Dune present, followed by whitespace/newlines, then Output (still valid)
    """Current message from X: Some initial commentary.
Dune: Spaced-out reply.


   
Output: Reply with extra blank lines before output.

NextSpeaker: Something else.""",

    # 15. Header present, but no Dune (only Output) – tests no Dune match
    """Current message from Z: Update from Z without Dune.
Status: System running.

Output: Should not match because no Dune block precedes it.

User: Done.""",

    # 16. Dune with Output but Output in lowercase and random whitespace
    """Current message from Laura: Quick lowercase test.
Dune: Lowercase test for Dune.

   output: lowercase output works too.

Mark: Done.""",

    # 17. Dune with no Output and trailing spaces/newlines
    """Current message from Victor: Trailing test incoming.
Dune: This Dune reply has no output.   
   
   
Alex: Next speaker.""",

    # 18. Dune with extra text before Output (should not capture Output)
    """Current message from Nina: Checking for intervening text.
Dune: Here is a note from Dune.
# Comment line before output
Ref: xyz

Output: Should not be captured because intervening text exists.

Beta: Next.""",

    # 19. Dune with Output, but next speaker in lowercase
    """Current message from Oscar: Lowercase speaker test.
Dune: Reply A.
Output: Captured output A.
alice: Next in lowercase.""",

    # 20. Dune with colon inside its text, then Output
    """Current message from Paul: Colon test scenario.
Dune: Value: 42 is the answer.
Output: Correct output for value.

User: Next.""",

    # 21. Dune with Output containing special characters
    """Current message from Quinn: Special chars incoming.
Dune: Special chars test.
Output: @$%^&*()_+ Output with symbols!

Admin: End.""",

    # 22. Two Dune blocks before a single Output (should capture only the first and no Output)
    """Current message from Rachel: Testing multiple Dune lines.
Dune: First line from Dune.
Dune: Second line from Dune.

Output: Should not be captured for the first because second Dune is treated as next speaker.

Sam: Next.""",

    # 23. Mixed-case "DuNe:" and mixed-case "OuTpUt:"
    """Current message from Sam: Mixed-case headers in play.
DuNe: Mixed case dune text.
OuTpUt: Mixed case output text.

Alex: Continue.""",

    # 24. Dune with extremely long text (repeated phrase) then Output
    """Current message from Tina: Long text test begins here.
""" + ("Dune: Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 5) + """
Output: Long text captured successfully.

Bob: Done.""",

    # 25. Two Dune blocks, first without Output, second with Output (should pick the first Dune only, no Output)
    """Current message from Uma: Testing two Dune blocks.
Dune: First reply without output.

Current message from Vince: Next block starts here.
Dune: Second reply with output.
Output: Second’s output.

Carl: Next.""",

    # 26. Dune and inline Output on the same line (no newline before Output)
    """Current message from Wendy: Inline testing now.
Dune: Inline test Output: Inline output should be captured.

Ana: Next.""",

    # 27. Extra text before "Current message" (junk) then a valid Dune+Output
    """Junk header text
More junk lines
Current message from Xavier: Finally a valid header.
Dune: Real message after junk.
Output: Should still match.

Yana: Next.""",

    # 28. Dune with empty text, then Output
    """Current message from Yvonne: Empty Dune test.
Dune:
Output: Only output, empty dune.

Zack: Next.""",

    # 29. No Dune in any block, multiple Headers (should not match anything)
    """Current message from Arthur: No dune this time.
Notice: No dune here.

Current message from Beth: Still no dune here either.
Status: Still no dune.

Output: This output should not match either.

Cathy: End.""",

    # 30. First Dune without Output, second Dune with Output (should pick only first Dune, no Output)
    """Current message from Dylan: Two-block test.
Dune: First message, no output.

Current message from Ethan: Second block starts.
Dune: Second message, has output.
Output: Second output.

Fiona: Next."""
]

for i, text in enumerate(test_cases, 1):
    print(f"\n--- Test Case {i} ---")
    check(text)
