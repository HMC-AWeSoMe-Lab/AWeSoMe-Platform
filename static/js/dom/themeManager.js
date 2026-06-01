import { appState } from '../services/appState.js';
import { domManager } from './domManager.js';
import { utils } from '../services/utils.js';

// Theme and settings initialization
export async function initializeTheme() {
    try {
        const settings = await utils.fetchJSON('/static/settings.json');
        const root = document.documentElement;
        
        // Apply theme settings
        Object.entries(settings.theme).forEach(([key, value]) => {
            root.style.setProperty(`--${key}`, value);
        });
        
        // Apply comment box settings
        Object.entries(settings.commentBox).forEach(([key, value]) => {
            if (key === 'borderColor') {
                root.style.setProperty('--borderColor', value);
            }
        });



        // Handle cancel button visibility
        const cancelButton = domManager.get('cancelButton');
        if (!settings.commentBox.displayCancel) {
            cancelButton.style.display = "none";
            const newCancelButton = cancelButton.cloneNode(true);
            cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
            domManager.set('cancelButton', newCancelButton);
        }
    } catch (error) {
        console.error("Error loading theme settings:", error);
    }


}