package com.example.service;

import org.springframework.stereotype.Service;
import java.util.List;
import java.util.ArrayList;

@Service
public class UserService {
    private final List<String> users = new ArrayList<>();

    public List<String> getAllUsers() {
        return new ArrayList<>(users);
    }

    public void addUser(String username) {
        users.add(username);
    }

    public boolean removeUser(String username) {
        return users.remove(username);
    }
} 