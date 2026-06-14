# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**

This tool searches the mock secondhand listings of data from the listings.json file.

**Input parameters:**

- `description` (str): The description of the item queried.
- `size` (str): The size of the item queried.
- `max_price` (float): The max price a user is willing to pay for a listing. 

**What it returns:**

The function will return matching items  that does not exceed max_price from query with fields of `id`, `title`, `description`, `category`, `style_tags`, `condition`, `price`, `colors`, `brand`, `platform`. 

**What happens if it fails or returns nothing:**

The agent should be able to return an empty [] and notify user "No listings found [under `{max_price}`] [in size `{ size }`]. Want me to broaden the search? ". If the tool itself fails (e.g., data cannot be loaded), return None.


---

### Tool 2: suggest_outfit

**What it does:**

This tool suggest new items to pair with the user's existing wardrobe, 'wardrobe_schema.json', to the user.

**Input parameters:**

- `new_item` (dict):  This parameter is the item to pair with item queried. 
- `wardrobe` (dict): This parameter represents the returned items from the `wardrobe_schema.json`

**What it returns:**

The return value for this function should be the new item from `search_listings()` and  a listing from `wardrobe_schema.json` with fields: `id`,`name`,`category `,`colors`,`style_tags`,`notes` to filtered suggestions. One or more complete outfit combinations should be suggested. 

**What happens if it fails or returns nothing:**

If the wardrobe is empty the agent should a value of empty[]. The agent response should be "Your wardrobe is empty — I can't suggest a pairing yet. Add some items to your wardrobe, or I can describe how to style this piece on its own." If the agent can not suggest an outfit, the value returned should be empty[]. The response should be "I couldn't find a strong match in your wardrobe for this item. Try adding more pieces, or broaden the style tags."
 
---

### Tool 3: create_fit_card

**What it does:**

This tool generates a review style comment that is sharable and short description of the outfit produced from new item.

**Input parameters:**

- `outfit` (str): This parameter represents the item retrieved by `suggest_outfit()`
- `new_item` (dict): This parameter represents the item for `search_listings()` 

*What it returns:**

 The agent should return a description of the items together, `[suggest_outfit]` + `[new item]` for review. 

 **What happens if it fails or returns nothing:**

The agent should return an `None` if the it fails, with a response "The fit card is empty. I can not suggest a review at this time. "
If the outfit data is incomplete, the agent should return a value `None`. The response should be from the agent "I want review my items right now, but I couldn't find complete outfit to share."


---

### Additional Tools (if any)


### Tool 4: price_comparison

**What it does:**

This tool ,given an item, estimates whether the price is fair based on comparable listings in the dataset.

**Input parameters:**

- `item` (dict): The price of the item 

**What it returns:**

The agent should return a value of a `lst[dict]`  that are comparable, share the same `category` and at least one `style_tag` with the selected item. - `id`,`description`,`size`,`max_price`,` title` ,`category`,`style_tags` ,`condition` , `brand` ,`platform` , ` colors`. The caparison results should be:
- `verdict` (str): "good deal", "fair", or "overpriced"`
- `avg_price` (float): average price of comparable items
- `cheaper_alternatives` (list[dict]): up to 2 cheaper listings with similar tags
Determination is by a threshold(-/+ 20%) against average price with good being below average, overpriced above average, otherwise fair.

**What happens if it fails or returns nothing:**

If the listing data is incomplete, the agent should return a value or `None`. The agent response should be " I can not offer a price comparison at this time. "

### Tool 5: style_profile

**What it does:**

Saves and retrieves a user's style preferences (sizes, preferred tags, categories) within the session so they don't re-describe their wardrobe each query. 

**Input parameters:**

- `action` (str):  This parameter save or load a user profile as a dict containing style data such size, preferred_tags, preferred_categories. 

**What it returns:**

The saved(`saved`) or loaded(`load`) profile dict, `_profile_store`, stored in `tools.py`, or an empty profile template if none exists will persists over the duration of the session. The dict resets at the begin of new session.

**Storage approach:**

Preferences are stored in a module-level dict (`_profile_store`) in `tools.py` that persists for the duration of the running app session. The dict resets to an empty template on app restart. Each tool call reads from and writes to this dict directly via the `"load"` and `"save"` actions.

**What happens if it fails or returns nothing:**

If no profile exists on "load", return an empty profile. Agent should respond with "User, describe your specific style. "

### Tool 6: popular_trends

**What it does:**

 Adds a tool that scans recent posts or tags,  via listings to highlight trending styles that match the user’s size range.

**Input parameters:**

- `category` (str) (optional):  This param represents category the popular item belongs to. 
- `size`(str) (optional):  This parameter represents the size of the trending item.

**What it returns:**

The agent returns a list[str] of top trending style_tags in filtered dataset.

**What happens if it fails or returns nothing:**

If no data matches the filters, return [] and skip trend commentary in the fit card.


## Planning Loop

**How does your agent decide which tool to call next?**

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

**Milestone 3 — Individual tool implementations:**

I plan to use Claude as my AI tool for this Milestone 3 implementation. I will give Claude the tools `search_listings`, `suggest_outfit`, and `create_fit_card` from the planning.md. I will ask Claude to implement each agent using load_listings from data loader. I will then test this against 3 queries before trusting it. 

**Milestone 4 — Planning loop and state management:**

 I will provide Claude with the instructions to complete a planning loop to help implement the tools. The expectations from Claude is to produce a diagram from the instructions which represents triggering of tools, how state flows between tools, and where error paths diverge. I will then test both against 3 queries before trusting it. 
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**

The agent will search first  check to see the user has an existing profile with `style_profile()`. If available the agent will load it and then search for the input query using the `search_listings()` and using data from listings.json. The input for this query would be `search_listings("vintage graphic tee", max_price=30.0)`. The agent returns matching listings of various sizes, sorted by relevance. 
**Step 2:**

The agent next,  will compare prices with the `price_comparison()` and not fore fit card. Then suggest an outfit using the `suggest_outfit()`. The input for this function is the queried item from step one, `new_item = <band tee>`,  and an item from the user's wardrobe , `wardrobe=<user's wardrobe>`. 
`suggest_outfit(new_item = <band tee>, wardrobe=<user's wardrobe> )`

**Step 3:**

Once the  `suggest_outfit()` has been call, popular_trends() can be called. If a trend is found, note for fit card. The agent then returns a Fit card, `create_fit_card(outfit=<suggestion>, new_item=<band tee>)`. This describes what platform the new item is from the listing, price comparison, the suggested closet wardrobe match and any trends captured.  

**Final output to user:**

The user should see a review style comment about the finding in the final outpost. 


## Spec Reflection 

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
Relying on the specifications before implementing any code, allowed for a overview of the project. The planning document served as a guideline and blueprint to implement each step and expectations of the project. 
**One way your implementation diverged from the spec, and why:**
The implementation of the specs diverged slightly from the project by implementing additional agents to be added to the planning loop. The additional tools added a user profile, price comparison, and trending topics to aid in assisting user queries. 
      
## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently? -->

**Instance 1**

- *What I gave the AI:*

Claude was given the planning loop section to review for logic flow for the project. It was directed to perform a logical review provide a visual for it.

- *What it produced:*

The AI companion produced a diagram which showed the loop of an item and how it moves between different agents.  

- *What I changed or overrode:*

The revised to make two tools optional within the planning loop as decided due to all users my not to save a profile or receive trend reports.  

**Instance 2**

- *What I gave the AI:*
 
Claude was provided the function handle_query with a TODO to review. It was directed to implement the function with those specs.

- *What it produced:*

 It produced a useable function for handling the projects queries for items within the entire loop.  

- *What I changed or overrode:*

The tool was revised to update `item ` within the tool. The update allowed for the catch of failure cases when `item ` is none.    