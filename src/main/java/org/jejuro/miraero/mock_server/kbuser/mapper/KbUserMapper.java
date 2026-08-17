package org.jejuro.miraero.mock_server.kbuser.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.jejuro.miraero.mock_server.kbuser.domain.KbUser;

@Mapper
public interface KbUserMapper {

    KbUser findByEmail(@Param("email") String email);

    KbUser findById(@Param("kbUserId") Long kbUserId);
}
