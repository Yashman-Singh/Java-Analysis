package com.example.controller;

import com.example.service.UserService;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping
    public List<String> getUsers() {
        return userService.getAllUsers();
    }

    @PostMapping
    public void addUser(@RequestBody String username) {
        userService.addUser(username);
    }

    @DeleteMapping("/{username}")
    public boolean removeUser(@PathVariable String username) {
        return userService.removeUser(username);
    }
} 