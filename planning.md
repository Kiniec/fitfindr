# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool searches the mock secondhand listings of data from the listings.json file.

**Input parameters:**
<!-- List each parameter, its type, and what it represents --> 
- `description` (str): The description of the item queried.
- `size` (str): The size of the item queried.
- `max_price` (float): The max price a user is willing to pay for a listing. 

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
The function will return matching items  that does not exceed max_price from query with fields of `id`, `title`, `description`, `category`, `style_tags`, `condition`, `price`, `colors`, `brand`, `platform`. 

**What happens if it fails or returns nothing:**

<!-- What should the agent do if no listings match? -->

The agent should be able to return an empty [] and notify user "No listings found [under `{max_price}`] [in size `{ size }`]. Want me to broaden the search? ". If the tool itself fails (e.g., data cannot be loaded), return None.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool suggest new items to pair with the user's existing wardrobe, 'wardrobe_schema.json', to the user.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict):  This parameter is the item to pair with item queried. 
- `wardrobe` (dict): This parameter represents the returned items from the `wardrobe_schema.json`

**What it returns:**
<!-- Describe the return value -->
The return value for this function should be the new item from `search_listings()` and  a listing from `wardrobe_schema.json` with fields: `id`,`name`,`category `,`colors`,`style_tags`,`notes` to filtered suggestions. One or more complete outfit combinations should be suggested. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty the agent should a value of empty[]. The agent response should be "Your wardrobe is empty — I can't suggest a pairing yet. Add some items to your wardrobe, or I can describe how to style this piece on its own." If the agent can not suggest an outfit, the value returned should be empty[]. The response should be "I couldn't find a strong match in your wardrobe for this item. Try adding more pieces, or broaden the style tags."
 
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool generates a review style comment that is sharable and short description of the outfit produced from new item.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): This parameter represents the item retrieved by `suggest_outfit()`
- `new_item` (dict): This parameter represents the item for `search_listings()` 

*What it returns:**
<!-- Describe the return value -->
 The agent should return a description of the items together, `[suggest_outfit]` + `[new item]` for review. 

 **What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
The agent should return an `None` if the it fails, with a response "The fit card is empty. I can not suggest a review at this time. "
If the outfit data is incomplete, the agent should return a value `None`. The response should be from the agent "I want review my items right now, but I couldn't find complete outfit to share."


---

### Additional Tools (if any)
<!-- Copy the block above for any tools beyond the required three -->

### Tool 4: price_comparison

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool ,given an item, estimates whether the price is fair based on comparable listings in the dataset.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `item` (dict): The price of the item 

**What it returns:**
<!-- Describe the return value -->
The agent should return a value of a `lst[dict]` holding the item that is the least expensive when compared to other listing. - `id`,`description`,`size`,`max_price`,` title` ,`category`,`style_tags` ,`condition` , `brand` ,`platform` , ` colors`. The caparison results should be:
- `verdict` (str): "good deal", "fair", or "overpriced"`
- `avg_price` (float): average price of comparable items
- `cheaper_alternatives` (list[dict]): up to 2 cheaper listings with similar tags


**What happens if it fails or returns nothing:**
<!-- What should the agent do if the data is incomplete? -->
If the listing data is incomplete, the agent should return a value or `None`. The agent response should be " I can not offer a price comparison at this time. "

### Tool 5: style_profile

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Saves and retrieves a user's style preferences (sizes, preferred tags, categories) within the session so they don't re-describe their wardrobe each query. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `action` (str):  This parameter save or load a user profile as a dict containing style data such size, preferred_tags, preferred_categories. 

**What it returns:**
<!-- Describe the return value -->
The saved or loaded profile dict, or an empty profile template if none exists.
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If no profile exists on "load", return an empty profile. Agent should respond with "User, describe your specific style. "

### Tool 6: popular_trends

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
 Adds a tool that scans recent posts or tags on a public fashion platform to highlight trending styles that match the user’s size range.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `category` (str) (optional):  This param represents category the popular item belongs to. 
- `size`(str) (optional):  This parameter represents the size of the trending item.

**What it returns:**
<!-- Describe the return value -->
The agent returns a list[str] of top trending style_tags in filtered dataset.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If no data matches the filters, return [] and skip trend commentary in the fit card.


## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->T
Load style_profile preload size/tag preferences to pre-fill search params, return and proceed to search_listings. 
After search_listings runs, check if results is empty. If yes, set an error message in the session and return early. If no, set selected_item = results[0] and pass list to price_comparison.
If search_listings returns [], retry once with size=None. If still empty, retry once more with size=None and max_price=None. After two retries with no results, notify the user.
Run price_comparison(selected_item), if overpriced, show cheaper alternatives long selected_item. If good deal, note in the fit card. return and proceed to suggest_outfit.
Run suggested_outfit. Check if results is empty. If yes, set an error message in the session and return early.  If no, out_suggestion = suggested_outfit, return and proceed to create_fit_card. 
(Optional) Call popular_trends. If selected_item's tags are trending, flag it in the fit card, return and proceed to create_fit_card.
Run create_fit_card, check if result is empty. If yes, set an error message in the session and return early. If no, fit_card = create_fit_card, return. 

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
Agent stores and access state within a session via a session dict at the start of each run_agent() call by way of new_session(). Data lives in memory in each transaction and returns to caller when done. The data that is being tracked are the queries, search_results, wardrobe, outfit_suggestion, fit_card, and errors. Each tool take only the specific data needed.  

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `style_profile` | No saved profile found | Use empty defaults; prompt user to describe their style after the interaction |
| `search_listings` | No listings match filters | Invoke `retry_logic`; if retries exhausted, tell user "No listings found [under $X] [in size Y]. Want me to broaden the search?" |
| `search_listings` | Data cannot be loaded (`None`) | Set `session["error"]`, stop: "Something went wrong loading listings. Please try again." |
| `retry_logic` | All retries exhausted, still `[]` | Stop and surface the final "No listings found" message to the user |
| `price_comparison` | No comparable listings to benchmark | Skip price verdict; proceed without mentioning value in the fit card |
| `suggest_outfit` | Wardrobe is empty | Stop: "Your wardrobe is empty — add items or I can style this piece on its own." |
| `suggest_outfit` | No strong pairing found | Stop: "No strong match in your wardrobe for this item. Try broadening style tags." |
| `popular_trends` | No trending tags found | Skip; do not mention trends in the fit card |
| `create_fit_card` | `outfit_suggestion` or `selected_item` is `None` | Stop: "I couldn't build a fit card — outfit data is incomplete." |




---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card, price_comparison, style_profile, popular_trends, retry_logic)↕ State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

 User query
    │
    ▼
Planning Loop
    │
    ├──► [Optional] style_profile("load") ──► preloads size / tag defaults into session
    │
    ▼
search_listings(description, size, max_price)
    │
    ├── [] ──► retry_logic: drop size, retry
    │               │
    │               ├── [] ──► retry_logic: drop max_price, retry
    │               │               │
    │               │               └── [] ──► STOP "No listings found."
    │               │
    │               └── results ──► selected_item = results[0]
    │
    └── results ──► selected_item = results[0]
                         │
                         ▼
              price_comparison(selected_item)
                         │
                         ├── overpriced ──► surface cheaper_alternatives alongside selected_item
                         │
                         └── fair / good deal ──► note for fit card
                                  │
                                  ▼
                    suggest_outfit(selected_item, wardrobe)
                                  │
                                  ├── wardrobe empty ──► STOP "Your wardrobe is empty..."
                                  ├── [] no match    ──► STOP "No strong match found..."
                                  │
                                  └── outfit_suggestion
                                            │
                                            ▼
                              [Optional] popular_trends(category, size)
                                            │
                                            ├── trending    ──► flag trend in fit card
                                            └── not trending ──► skip
                                                      │
                                                      ▼
                              create_fit_card(outfit_suggestion, selected_item)
                                                      │
                                                      ├── None ──► STOP "Fit card is empty..."
                                                      │
                                                      └── fit_card (str)
                                                                │
                                                                ▼
                                                       Return fit card to user ✓ 

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->



**Milestone 3 — Individual tool implementations:**

I plan to use Claude as my AI tool for this Milestone 3 implementation. I will give Claude the tools `search_listings`, `suggest_outfit`, and `create_fit_card` from the planning.md. I will ask Claude to implement each agent using load_listings from data loader. I will then test this against 3 queries before trusting it. 

**Milestone 4 — Planning loop and state management:**
 I will provide Claude with the instructions to complete a planning loop to help implement the tools. The expectations from Claude is to produce a diagram from the instructions which represents triggering of tools, how state flows between tools, and where error paths diverge. I will then test both against 3 queries before trusting it. 

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent will search first  check to see the user has an existing profile with `style_profile()`. If available the agent will load it and then search for the input query using the `search_listings()` and using data from listings.json. The input for this query would be `search_listings("vintage graphic tee", max_price=30.0)`. The agent returns matching listings of various sizes, sorted by relevance. 
**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
The agent next,  will compare prices with the `price_comparison()` and not fore fit card. Then suggest an outfit using the `suggest_outfit()`. The input for this function is the queried item from step one, `new_item = <band tee>`,  and an item from the user's wardrobe , `wardrobe=<user's wardrobe>`. 
`suggest_outfit(new_item = <band tee>, wardrobe=<user's wardrobe> )`
**Step 3:**
<!-- Continue until the full interaction is complete -->
Once the  `suggest_outfit()` has been call, popular_trends() can be called. If a trend is found, note for fit card. The agent then returns a Fit card, `create_fit_card(outfit=<suggestion>, new_item=<band tee>)`. This describes what platform the new item is from the listing, price comparison, the suggested closet wardrobe match and any trends captured.  
**Final output to user:**
<!-- What does the user actually see at the end? -->
The user should see a review style comment about the finding in the final outpost. 