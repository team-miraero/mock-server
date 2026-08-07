package org.jejuro.miraero.mock_server.oauth.store;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

@Component
public class OAuthStore {

    private final Map<String, Entry> authorizationCodes = new ConcurrentHashMap<>();
    private final Map<String, Entry> accessTokens = new ConcurrentHashMap<>();

    public void saveAuthorizationCode(String code, Long kbUserId, long ttlSeconds) {
        authorizationCodes.put(code, new Entry(kbUserId, Instant.now().plusSeconds(ttlSeconds)));
    }

    /** 유효하면 kbUserId를 반환하며 코드를 소비한다. 유효하지 않으면 null. */
    public Long consumeAuthorizationCode(String code) {
        Entry entry = authorizationCodes.remove(code);
        if (entry == null || entry.isExpired()) {
            return null;
        }
        return entry.kbUserId();
    }

    public void saveAccessToken(String accessToken, Long kbUserId, long ttlSeconds) {
        accessTokens.put(accessToken, new Entry(kbUserId, Instant.now().plusSeconds(ttlSeconds)));
    }

    /** 유효하면 kbUserId를 반환한다. 유효하지 않으면 null. */
    public Long findKbUserIdByAccessToken(String accessToken) {
        Entry entry = accessTokens.get(accessToken);
        if (entry == null) {
            return null;
        }
        if (entry.isExpired()) {
            accessTokens.remove(accessToken);
            return null;
        }
        return entry.kbUserId();
    }

    private record Entry(Long kbUserId, Instant expiresAt) {

        boolean isExpired() {
            return Instant.now().isAfter(expiresAt);
        }
    }
}
