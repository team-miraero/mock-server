package org.jejuro.miraero.mock_server.kbuser.mapper;

import static org.assertj.core.api.Assertions.assertThat;

import org.jejuro.miraero.mock_server.kbuser.domain.KbUser;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class KbUserMapperTest {

    @Autowired
    private KbUserMapper kbUserMapper;

    @Test
    @DisplayName("이메일로 KB 사용자를 조회한다")
    void findByEmail() {
        KbUser kbUser = kbUserMapper.findByEmail("miraero01@test.com");

        assertThat(kbUser).isNotNull();
        assertThat(kbUser.getKbUserId()).isEqualTo(10001L);
    }

    @Test
    @DisplayName("존재하지 않는 이메일이면 null을 반환한다")
    void findByEmail_notFound() {
        assertThat(kbUserMapper.findByEmail("nobody@example.com")).isNull();
    }
}
