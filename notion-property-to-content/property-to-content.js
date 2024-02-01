#!/usr/bin/env node

import { Client } from "@notionhq/client";
import { markdownToBlocks, markdownToRichText } from "@tryfabric/martian";
import dotenv from "dotenv";
import { inspect } from "util";

// Load environment variables
dotenv.config();

/**
 * Print out an object and all of its children
 */
function inspectFull(myObj) {
    console.log(inspect(myObj, {showHidden: false, depth: null, colors: true}))
}

if (process.argv.length < 4) {
  console.error(
    "Usage: node property-to-content.js <database-id> <property> [--remove]"
  );
  process.exit(1);
}

const token = process.env.NOTION_TOKEN;

if (!token) {
  console.error("Missing NOTION_TOKEN in environment");
  process.exit(1);
}

const id = process.argv[2];
const property = process.argv[3];
const remove = process.argv[4] === "--remove";

const notion = new Client({
  auth: token,
});

async function* paginate(method, params) {
  const result = await method(params);

  yield result;

  if (result.next_cursor) {
    yield* paginate(method, { ...params, start_cursor: result.next_cursor });
  }
}

async function processPage(page) {
  if (!page.properties[property]) {
    return;
  }

  const richText = page.properties[property].rich_text;

  if (!richText || richText.length < 1) {
    return;
  }

  let children = richText;

  // Single text node, try to parse it
  if (richText.length === 1) {
    children = markdownToBlocks(richText[0].plain_text);
  }

  const title = page.properties.Name.title[0].plain_text;
  console.log(`Processing: ${title}`);

  await notion.blocks.children.append({
    block_id: page.id,
    children,
  });

  if (remove) {
    notion.pages.update({
      page_id: page.id,
      properties: {
        [property]: {
          rich_text: [],
        },
      },
    });
  }
}

// TEST
const nathair = `You fill a 20-foot cube centered on a point you choose within range with fey and draconic magic. Roll on the Mischievous Surge table to determine the magical effect produced. At the start of each of your turns, you can move the cube up to 10 feet and reroll on the table.

| **Mischievous Surge** | |
| --- | --- |
| **d4** | **Effect** |
| 1 | The smell of apple pie fills the air, and each creature in the cube must succeed on a Wisdom saving throw or become charmed by you until the start of your next turn. |
| 2 | Bouquets of flowers appear all around, and each creature in the cube must succeed on a Dexterity saving throw or be blinded until the start of your next turn as the flowers spray water in their faces. |
| 3 | Each creature in the cube must succeed on a Wisdom saving throw or begin giggling until the start of your next turn. A giggling creature is incapacitated and uses all its movement to move in a random direction. |
| 4 | Drops of molasses appear and hover in the cube, turning it into difficult terrain until the start of your next turn. |
`;
const chaosBolt = `You hurl an undulating, warbling mass of chaotic energy at one creature in range. Make a ranged spell attack against the target. On a hit, the target takes 2d8 + 1d6 damage. Choose one of the d8s. The number rolled on that die determines the attack's damage type, as shown below.

| d8 | Damage Type |
| --- | --- |
| 1 | Acid |
| 2 | Cold |
| 3 | Fire |
| 4 | Force |
| 5 | Lightning |
| 6 | Poison |
| 7 | Psychic |
| 8 | Thunder |


If you roll the same number on both d8s, the chaotic energy leaps from the target to a different creature of your choice within 30 feet of it. Make a new attack roll against the new target, and make a new damage roll, which could cause the chaotic energy to leap again.

A creature can be targeted only once by each casting of this spell.
`
inspectFull(markdownToBlocks(nathair));
//const testPageId = "d41d26f9b86c46eeb6d05a8892a2dc6d"
//const page = await notion.pages.retrieve({ page_id: testPageId })
//await processPage(page)
process.exit();

const iterator = paginate(notion.databases.query, { database_id: id });

for await (const query of iterator) {
  for (const page of query.results) {
    await processPage(page);
  }
}
