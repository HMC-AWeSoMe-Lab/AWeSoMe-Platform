// 📦 DOM Modules
import { domManager } from './dom/domManager.js';
import { initializeTheme } from './dom/themeManager.js';

// ⚡ Event Setup
import { setupEventListeners, setupInterventionTriggers } from './events/eventSetup.js';
import { toggleCommentBox } from './events/commentActions.js';

// 🎯 Interventions
import { initializeHighlighting } from './interventions/highlighting.js';
import { interventionHandlers } from './interventions/interventionHandlers.js';

// 🛠 Services & State
import { getId, idToMode, start, initializeReplyStyle } from './services/apiService.js';
import { appState } from './services/appState.js';
import { pushToPayloadQueue } from './services/payloadQueue.js';

import { initCommentLengthGuard } from './events/commentActions.js';

// alongside your other init calls e.g. initializeHighlighting(), etc.
initCommentLengthGuard();

/**
 * Logs intervention text to the payload queue for database storage.
 * Automatically extracts text from any intervention type in a generic way.
 * 
 * @param {Object} interventionData - The intervention data containing type and content
 * @returns {Promise<void>} Promise that resolves when text is logged
 */
async function logInterventionText(interventionData) {
  console.log("🔍 logInterventionText called with:", interventionData);
  let interventionTexts = [];
  
  // Method 1: Check if there's a direct 'text' property in intervention data
  if (interventionData.text && typeof interventionData.text === 'string') {
    interventionTexts.push(interventionData.text.trim());
    console.log("✅ Found direct text property:", interventionData.text);
  }
  
  // Method 2: Extract from HTML if present
  if (interventionData.html) {
    console.log("🔍 Analyzing HTML:", interventionData.html);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = interventionData.html;
    
    // Generic text extraction strategies
    const extractedTexts = [];
    
    // Strategy 1: Look for common text-containing elements
    const textSelectors = [
      'p',           // paragraphs (common in popups)
      '[id*="text"]', // elements with "text" in their ID
      '[class*="text"]', // elements with "text" in their class
      '.content',    // content divs
      '.message',    // message divs
      '.feedback',   // feedback elements
      'span'         // spans that might contain text
    ];
    
    for (const selector of textSelectors) {
      const elements = tempDiv.querySelectorAll(selector);
      console.log(`🔍 Found ${elements.length} elements for selector "${selector}"`);
      elements.forEach(element => {
        const text = element.textContent?.trim();
        if (text && text.length > 0) {
          console.log(`📝 Text found in ${selector}:`, text);
          // Avoid duplicates and button text
          const isButton = element.tagName.toLowerCase() === 'button' || 
                          element.closest('button') ||
                          text.toLowerCase().includes('close') ||
                          text.toLowerCase().includes('button');
          
          if (!isButton && !extractedTexts.includes(text)) {
            extractedTexts.push(text);
            console.log("✅ Added text to extraction list:", text);
          } else {
            console.log("❌ Skipped text (button or duplicate):", text);
          }
        }
      });
    }
    
    // Strategy 2: If no specific elements found, get all non-button text
    if (extractedTexts.length === 0) {
      console.log("🔍 No specific elements found, trying fallback extraction");
      // Remove button elements and scripts before getting text
      const buttonsAndScripts = tempDiv.querySelectorAll('button, script, style');
      buttonsAndScripts.forEach(el => el.remove());
      
      const allText = tempDiv.textContent?.trim();
      if (allText && allText.length > 0) {
        extractedTexts.push(allText);
        console.log("✅ Fallback extraction found:", allText);
      }
    }
    
    interventionTexts.push(...extractedTexts);
  }
  
  // Method 3: Check for other common text properties
  const textProperties = ['message', 'content', 'description', 'body'];
  for (const prop of textProperties) {
    if (interventionData[prop] && typeof interventionData[prop] === 'string') {
      const text = interventionData[prop].trim();
      if (text && !interventionTexts.includes(text)) {
        interventionTexts.push(text);
        console.log(`✅ Found text in property "${prop}":`, text);
      }
    }
  }
  
  console.log("📋 Final intervention texts to log:", interventionTexts);
  
  // Log each unique piece of intervention text found
  for (const interventionText of interventionTexts) {
    if (interventionText && interventionText.length > 0) {
      const actionType = `${interventionData.type.toUpperCase()}_TEXT`;
      
      console.log(`📝 About to log: ${actionType} -> ${interventionText}`);
      
      // Set the latest action in app state
      appState.setLatestAction(actionType, interventionText);
      
      // Push to payload queue
      await pushToPayloadQueue();
      
      console.log(`✅ Successfully logged intervention text to queue:`, {
        type: actionType,
        text: interventionText,
        interventionType: interventionData.type
      });
    }
  }
  
  if (interventionTexts.length === 0) {
    console.log("⚠️ No intervention text found to log");
  }
}

/**
 * Triggers interventions based on user actions and text input.
 * Sends data to the backend /interventions endpoint and processes the response.
 * 
 * @param {string} draft - The current text content being analyzed
 * @param {string} interactionId - Unique identifier for the current interaction
 * @param {string} triggerEvent - Type of event triggering interventions (e.g., "onClick", "onText", "onLoad")
 * @param {string|null} [buttonID=null] - ID of the button that was clicked (for onClick events)
 * @returns {Promise<void>} Promise that resolves when all interventions are processed
 */
export async function triggerInterventions(draft, interactionId, triggerEvent, buttonID = null) {
  console.log("Triggering interventions:", { draft, interactionId, triggerEvent, buttonID });
  try {
    const res = await fetch('/interventions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: draft,
        latestID: interactionId,
        currentTimestamp: Date.now(),
        triggerEvent,
        buttonID
      })
    });

    // Check if the response indicates an intervention configuration error
    if (!res.ok) {
      const errorData = await res.json();
      if (errorData.interventionError) {
        // Display friendly error to user
        console.error("❌ Intervention Configuration Error:", errorData.error);
        alert(`⚠️ Intervention Setup Problem:\n\n${errorData.error}\n\nPlease check your intervention configuration.`);
        return;
      } else {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
    }

    const interventions = await res.json();

    for (const data of interventions) {
      console.log("Processing intervention data:", data.triggerEvent);
      if (!data || data.triggerEvent !== triggerEvent) continue;
      
      // Log intervention text before processing the intervention
      await logInterventionText(data);
      
      const handler = interventionHandlers[data.type];
      if (handler) handler(data);
      else console.warn(`⚠️ No handler for type: ${data.type}`);
    }
  } catch (error) {
    console.error("❌ Error triggering interventions:", error);
    // Display a user-friendly error message
    console.error("Failed to load interventions. Please check the console for details.");
  }
}

/**
 * Initializes the application by setting up user session and starting core services.
 * Handles user ID generation, mode assignment, and conversation startup.
 * 
 * @returns {Promise<void>} Promise that resolves when app initialization is complete
 */
async function initializeApp() {
  try {
    await getId();
    await idToMode();
    await start();
  } catch (error) {
    console.error("Error during app initialization:", error);
  }
}

/**
 * Initializes DOM elements and sets up event listeners.
 * Configures theme, intervention triggers, and reply styles after DOM is ready.
 * 
 * @returns {Promise<void>} Promise that resolves when DOM initialization is complete
 */
async function initializeDOM() {
  try {
    domManager.initialize();
    setupEventListeners();
    setupInterventionTriggers();
    await initializeTheme();
    await initializeReplyStyle();
  } catch (error) {
    console.error("Error during DOM initialization:", error);
  }
}

/**
 * Page load event handler.
 * Initializes the application and triggers onLoad interventions.
 * 
 * @returns {Promise<void>} Promise that resolves when page load setup is complete
 */
window.onload = async function () {
  await initializeApp();
  // Trigger onLoad interventions after app initialization
  triggerInterventions("", appState.latestID, "onLoad");
};

/**
 * DOM content loaded event handler.
 * Sets up DOM elements and event listeners when the document is ready.
 * 
 * @returns {Promise<void>} Promise that resolves when DOM content setup is complete
 */
document.addEventListener('DOMContentLoaded', async function () {
  await initializeDOM();
});


//
// Expose for debugging/dev
//
window.triggerInterventions = triggerInterventions;
window.toggleCommentBox = toggleCommentBox;

