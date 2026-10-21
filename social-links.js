"use strict";

// Only these profiles can be opened by the redirect page.
const socialProfiles = [
    ["discord", "Discord", "https://discord.com/users/205816662530719744"],
    ["tiktok", "TikTok", "https://www.tiktok.com/@zincodron3"],
    ["github", "GitHub", "https://www.github.com/zincodrone"],
    ["bluesky", "Bluesky", "https://bsky.app/profile/zinco.gay"],
    ["x", "Twitter / X", "https://x.com/zincodrone"],
    ["youtube", "YouTube", "https://www.youtube.com/@Z_NCO"],
    ["twitch", "Twitch", "https://www.twitch.tv/zincodrone"],
    ["instagram", "Instagram", "https://www.instagram.com/zincodrone/"],
];

const choice = document.getElementById("social-choice");
if (choice && typeof choice.showModal === "function") {
    let selectedProfile;
    let trigger;
    document.querySelectorAll(".social-links a").forEach((link) => {
        link.addEventListener("click", (event) => {
            // Preserve browser shortcuts such as Ctrl-click and Cmd-click.
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
            const profile = socialProfiles.find((item) => item[2] === link.href);
            if (!profile) return;
            event.preventDefault();
            selectedProfile = profile;
            trigger = link;
            document.getElementById("choice-description").textContent = `Open ${profile[1]} in this tab or a new tab?`;
            choice.showModal();
        });
    });
    document.getElementById("open-current").addEventListener("click", () => {
        window.location.assign(`/redirect?social=${encodeURIComponent(selectedProfile[0])}`);
    });
    document.getElementById("open-new").addEventListener("click", () => {
        window.open(selectedProfile[2], "_blank", "noopener,noreferrer");
        choice.close();
    });
    document.getElementById("cancel-choice").addEventListener("click", () => choice.close());
    choice.addEventListener("close", () => trigger?.focus());
}

const destination = document.getElementById("redirect-destination");
if (destination) {
    const profile = socialProfiles.find((item) => item[0] === new URLSearchParams(window.location.search).get("social"));
    const status = document.getElementById("redirect-status");
    const continueLink = document.getElementById("continue-social");
    if (profile) {
        destination.textContent = `You're heading to ${profile[1]}.`;
        document.getElementById("redirect-url").textContent = profile[2];
        continueLink.href = profile[2];
        continueLink.hidden = false;
        status.textContent = "Opening your profile destination in 5 seconds…";
        const redirectTimer = window.setTimeout(() => window.location.replace(profile[2]), 5000);
        document.getElementById("cancel-redirect").addEventListener("click", () => window.clearTimeout(redirectTimer));
        window.addEventListener("pagehide", () => window.clearTimeout(redirectTimer), { once: true });
    } else {
        destination.textContent = "No social profile selected.";
        status.textContent = "Return to Socials to choose a profile.";
    }
}
