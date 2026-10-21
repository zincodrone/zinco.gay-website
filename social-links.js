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
if (choice) {
    let selectedProfile;
    let trigger;
    let revealAnimation;
    function closeChoice() {
        revealAnimation?.cancel();
        choice.hidden = true;
        trigger?.focus({ preventScroll: true });
    }
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
            const wasHidden = choice.hidden;
            choice.hidden = false;
            if (wasHidden && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
                revealAnimation?.cancel();
                revealAnimation = choice.animate(
                    [{ height: "0px", opacity: 0 }, { height: `${choice.scrollHeight}px`, opacity: 1 }],
                    { duration: 400, easing: "cubic-bezier(0.2, 0.8, 0.2, 1)" }
                );
                revealAnimation.addEventListener("finish", () => {
                    choice.scrollIntoView({ behavior: "smooth", block: "nearest" });
                }, { once: true });
            }
            document.getElementById("choice-title").focus({ preventScroll: true });
            if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
                choice.scrollIntoView({ behavior: "auto", block: "nearest" });
            }
        });
    });
    document.getElementById("open-current").addEventListener("click", () => {
        window.location.assign(`/redirect?social=${encodeURIComponent(selectedProfile[0])}`);
    });
    document.getElementById("open-new").addEventListener("click", () => {
        window.open(selectedProfile[2], "_blank", "noopener,noreferrer");
        closeChoice();
    });
    document.getElementById("cancel-choice").addEventListener("click", closeChoice);
    choice.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            event.preventDefault();
            closeChoice();
        }
    });
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
        const redirectAt = Date.now() + 5000;
        let lastSeconds;
        function updateCountdown() {
            const seconds = Math.max(0, Math.ceil((redirectAt - Date.now()) / 1000));
            if (seconds === lastSeconds) return;
            lastSeconds = seconds;
            status.textContent = seconds > 0
                ? `Opening your profile destination in ${seconds} ${seconds === 1 ? "second" : "seconds"}…`
                : "Opening your profile destination now…";
            if (seconds === 0) {
                window.clearInterval(redirectTimer);
                window.location.replace(profile[2]);
            }
        }
        const redirectTimer = window.setInterval(updateCountdown, 250);
        updateCountdown();
        const stopCountdown = () => window.clearInterval(redirectTimer);
        document.getElementById("cancel-redirect").addEventListener("click", stopCountdown);
        continueLink.addEventListener("click", stopCountdown);
        window.addEventListener("pagehide", stopCountdown, { once: true });
    } else {
        destination.textContent = "No social profile selected.";
        status.textContent = "Return to Socials to choose a profile.";
    }
}
