import fs from 'fs';
import path from 'path';
import { parse } from 'node-html-parser';

interface CardData {
  [slug: string]: string;
}

interface Player {
  username: string;
  captain: string;
  deck: string[];
}

interface EventData {
  event: {
    id: string;
    name: string;
    date: string;
    total_champions: number;
  };
  players: Player[];
}

function extractSlug(href: string): string {
  const match = href.match(/\/cards\/([^/]+)\/?/);
  if (!match) {
    throw new Error(`Could not extract slug from href: ${href}`);
  }
  return match[1];
}

function parseEvent(htmlFilePath: string, eventId: string): {
  eventData: EventData;
  cardsData: CardData;
  newCardsCount: number;
} {
  const html = fs.readFileSync(htmlFilePath, 'utf-8');
  const root = parse(html);

  // Extract event metadata
  const h1 = root.querySelector('h1');
  const eventName = h1?.textContent.trim() || '';

  const timeTag = root.querySelector('time');
  const eventDate = timeTag?.getAttribute('datetime')?.split('T')[0] || '';

  // Extract total champions from prose paragraph
  const proseParagraph = root.querySelectorAll('p').find((p) =>
    p.textContent.includes('players were crowned')
  );
  const championsMatch = proseParagraph?.textContent.match(/(\d+)\s+players were crowned/);
  const totalChampions = championsMatch ? parseInt(championsMatch[1], 10) : 0;

  // Extract player data
  const champInfoElements = root.querySelectorAll('.champ-info');
  const players: Player[] = [];
  const cardsMap: CardData = {};

  for (const champInfo of champInfoElements) {
    // Extract username
    const champName = champInfo.querySelector('.champ-name');
    const username = champName?.textContent.trim() || '';

    // Extract captain
    const captainDiv = champInfo.querySelector('.champ-captain');
    const captainLink = captainDiv?.querySelector('a');
    const captainHref = captainLink?.getAttribute('href') || '';
    const captainSlug = extractSlug(captainHref);
    const captainName = captainLink?.textContent.trim() || '';

    // Add captain to cards map
    if (captainSlug && captainName) {
      cardsMap[captainSlug] = captainName;
    }

    // Extract deck cards
    const deckCards: string[] = [];
    const cardsList = champInfo.querySelector('.cards-list');

    if (cardsList) {
      const cardLinks = cardsList.querySelectorAll('a');

      for (const cardLink of cardLinks) {
        const href = cardLink.getAttribute('href') || '';
        const cardSlug = extractSlug(href);
        const cardName = cardLink.textContent.trim();

        if (cardSlug && cardName) {
          deckCards.push(cardSlug);
          cardsMap[cardSlug] = cardName;
        }
      }
    }

    players.push({
      username,
      captain: captainSlug,
      deck: deckCards,
    });
  }

  const eventData: EventData = {
    event: {
      id: eventId,
      name: eventName,
      date: eventDate,
      total_champions: totalChampions,
    },
    players,
  };

  // Load existing cards.json if it exists
  const cardsJsonPath = path.join(process.cwd(), 'src/data/cards.json');
  let existingCards: CardData = {};

  if (fs.existsSync(cardsJsonPath)) {
    const existingContent = fs.readFileSync(cardsJsonPath, 'utf-8');
    existingCards = JSON.parse(existingContent);
  }

  // Merge new cards (never overwrite existing entries)
  let newCardsCount = 0;

  for (const [slug, name] of Object.entries(cardsMap)) {
    if (!(slug in existingCards)) {
      existingCards[slug] = name;
      newCardsCount++;
    }
  }

  return {
    eventData,
    cardsData: existingCards,
    newCardsCount,
  };
}

function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: node scripts/parse-event.js <html-file> <event-id>');
    process.exit(1);
  }

  const [htmlFilePath, eventId] = args;

  if (!fs.existsSync(htmlFilePath)) {
    console.error(`Error: File not found: ${htmlFilePath}`);
    process.exit(1);
  }

  try {
    const { eventData, cardsData, newCardsCount } = parseEvent(htmlFilePath, eventId);

    // Ensure directories exist
    const eventsDir = path.join(process.cwd(), 'src/data/events');
    const dataDir = path.join(process.cwd(), 'src/data');

    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }

    if (!fs.existsSync(eventsDir)) {
      fs.mkdirSync(eventsDir, { recursive: true });
    }

    // Write event JSON
    const eventJsonPath = path.join(eventsDir, `${eventId}.json`);
    fs.writeFileSync(eventJsonPath, JSON.stringify(eventData, null, 2));
    console.log(`✓ Wrote ${eventJsonPath}`);

    // Write cards JSON
    const cardsJsonPath = path.join(dataDir, 'cards.json');
    fs.writeFileSync(cardsJsonPath, JSON.stringify(cardsData, null, 2));
    console.log(`✓ Wrote ${cardsJsonPath}`);

    // Log summary
    console.log(`\nSummary:`);
    console.log(`  Players parsed: ${eventData.players.length}`);
    console.log(`  New cards added: ${newCardsCount}`);
  } catch (error) {
    console.error('Error parsing event:', error);
    process.exit(1);
  }
}

main();
